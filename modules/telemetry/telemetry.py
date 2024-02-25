# Telemetry to parse radio packets, keep history and to log everything
# Incoming information comes from rn2483_radio_payloads in payload format
# Outputs information to telemetry_json_output in friendly json for UI
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)
from dataclasses import dataclass
from io import BufferedWriter
import logging
import math
from ast import literal_eval
from queue import Queue
import multiprocessing as mp
from multiprocessing import Process, active_children
from pathlib import Path

from signal import signal, SIGTERM
from time import time, sleep
from typing import Any, TypeAlias

import modules.telemetry.json_packets as jsp
import modules.websocket.commands as wsc
from modules.misc.config import Config
from modules.telemetry.replay import TelemetryReplay
from modules.telemetry.sd_block import LoggingMetadataSpacerBlock
from modules.telemetry.superblock import SuperBlock, Flight
from modules.telemetry.telemetry_utils import (
    mission_path,
    get_filepath_for_proposed_name,
    parse_rn2483_transmission,
    ParsedBlock,
)
from modules.telemetry.telemetry_errors import MissionNotFoundError, AlreadyRecordingError, ReplayPlaybackError

# Types

JSON: TypeAlias = dict[str, Any]

# Constants
ORG: str = "CUInSpace"
VERSION: str = "0.5.1-DEV"
MISSION_EXTENSION: str = "mission"
FILE_CREATION_ATTEMPT_LIMIT: int = 50
SUPPORTED_ENCODING_VERSION: int = 1

# Set up logging
logger = logging.getLogger(__name__)


def shutdown_sequence() -> None:
    for child in active_children():
        child.terminate()
    exit(0)


# Main class
class Telemetry(Process):
    def __init__(
        self,
        serial_status: Queue[str],
        radio_payloads: Queue[Any],
        rn2483_radio_input: Queue[str],
        radio_signal_report: Queue[str],
        telemetry_json_output: Queue[JSON],
        telemetry_ws_commands: Queue[list[str]],
        config: Config,
    ):
        super().__init__()
        self.config = config

        self.radio_payloads: Queue[str] = radio_payloads
        self.telemetry_json_output: Queue[JSON] = telemetry_json_output
        self.telemetry_ws_commands: Queue[list[str]] = telemetry_ws_commands
        self.rn2483_radio_input: Queue[str] = rn2483_radio_input
        self.radio_signal_report: Queue[str] = radio_signal_report
        self.serial_status: Queue[str] = serial_status

        # Telemetry Data holds the last few copies of received data blocks stored under the subtype name as a key.
        self.status: jsp.StatusData = jsp.StatusData()
        self.telemetry: dict[str, list[dict[str, str]]] = {}

        # Mission System
        self.missions_dir = Path.cwd().joinpath("missions")
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.mission_path: Path | None = None

        # Mission Recording
        self.mission_recording_file: BufferedWriter | None = None
        self.mission_recording_sb: SuperBlock = SuperBlock()
        self.mission_recording_buffer: bytearray = bytearray(b"")

        # Replay System
        self.replay = None
        self.replay_input: Queue[str] = mp.Queue()  # type:ignore
        self.replay_output: Queue[tuple[int, int, str]] = mp.Queue()  # type:ignore

        # Handle program closing to ensure no orphan processes
        signal(SIGTERM, shutdown_sequence)  # type:ignore

        # Start Telemetry
        self.update_websocket()
        self.run()

    def run(self):
        while True:
            # Sleep for 1 ms
            sleep(0.001)

            while not self.telemetry_ws_commands.empty():
                # Parse websocket command into an enum
                commands: list[str] = self.telemetry_ws_commands.get()
                command = wsc.parse(commands, wsc.WebsocketCommand)
                parameters = commands  # Remaining items in the commands list are parameters
                try:
                    self.execute_command(command, parameters)
                except AttributeError as e:
                    logger.error(e)

            while not self.radio_signal_report.empty():
                # TODO set radio SNR
                logger.info(f"SIGNAL DATA {self.radio_signal_report.get()}")

            while not self.serial_status.empty():
                x = self.serial_status.get().split(" ", maxsplit=1)
                logger.debug(f"serial_status: {x}")
                self.parse_serial_status(command=x[0], data=x[1])
                self.update_websocket()

            # Switch data queues between replay and radio depending on mission state
            match self.status.mission.state:
                case jsp.MissionState.RECORDED:
                    while not self.replay_output.empty():
                        block_type, block_subtype, block_data = self.replay_output.get()  # type: ignore
                        # logger.debug(("IGNORE", block_type, block_subtype))
                        # self.parse_rn2483_payload(block_type, block_subtype, block_data)
                        # self.parse_rn2483_transmission(block_data)
                        self.process_transmission(block_data)
                        self.update_websocket()
                case _:
                    while not self.radio_payloads.empty():
                        # self.parse_rn2483_transmission(self.radio_payloads.get())
                        self.process_transmission(self.radio_payloads.get())
                        self.update_websocket()

    def update_websocket(self) -> None:
        """Updates the websocket with the latest packet using the JSON output process."""
        websocket_response = {"version": VERSION, "org": ORG, "status": dict(self.status), "telemetry": self.telemetry}
        self.telemetry_json_output.put(websocket_response)

    def reset_data(self) -> None:
        """Resets all live data on the telemetry backend to a default state."""
        self.status = jsp.StatusData()
        self.telemetry = {}

    def parse_serial_status(self, command: str, data: str) -> None:
        """Parses the serial managers status output"""
        match command:
            case "serial_ports":
                self.status.serial.available_ports = literal_eval(data)
            case "rn2483_connected":
                self.status.rn2483_radio.connected = bool(data)
            case "rn2483_port":
                if self.status.mission.state != jsp.MissionState.DNE:
                    self.reset_data()
                self.status.rn2483_radio.connected_port = data

                match self.status.rn2483_radio.connected_port:
                    case "":
                        self.status.mission.state = jsp.MissionState.DNE
                    case _:
                        self.status.mission.state = jsp.MissionState.LIVE
            case _:
                return None

    def execute_command(self, command: wsc.Enum, parameters: list[str]) -> None:
        """Executes the passed websocket command."""

        WSCommand = wsc.WebsocketCommand
        match command:
            case WSCommand.UPDATE:
                self.status.replay.update_mission_list()

            # Replay commands
            case WSCommand.REPLAY.value.PLAY:
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.play_mission(mission_name)
                except MissionNotFoundError as e:
                    logger.error(e.message)
                except ReplayPlaybackError as e:
                    logger.error(e.message)
            case WSCommand.REPLAY.value.PAUSE:
                self.set_replay_speed(0.0)
            case WSCommand.REPLAY.value.RESUME:
                self.set_replay_speed(self.status.replay.last_played_speed)
            case WSCommand.REPLAY.value.SPEED:
                self.set_replay_speed(float(parameters[0]))
            case WSCommand.REPLAY.value.STOP:
                self.stop_replay()

            # Record commands
            case WSCommand.RECORD.value.STOP:
                self.stop_recording()
            case WSCommand.RECORD.value.START:
                # If there is no mission name, use the default
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.start_recording(mission_name)
                except AlreadyRecordingError as e:
                    logger.error(e.message)
                except ReplayPlaybackError as e:
                    logger.error(e.message)
            case _:
                raise NotImplementedError(f"Command {command} not implemented.")

        self.update_websocket()

    def set_replay_speed(self, speed: float):
        """Set the playback speed of the replay system."""
        try:
            speed = 0.0 if float(speed) < 0 else float(speed)
        except ValueError:
            speed = 0.0

        # Keeps last played speed updated while preventing it from hitting 0 if past speed is 0
        self.status.replay.last_played_speed = self.status.replay.speed if self.status.replay.speed != 0.0 else 1
        self.status.replay.speed = speed

        # Set replay status based on speed
        # If mission is not recorded, replay should be in DNE state.
        # if else, set to pause/playing based on speed
        if self.status.mission.state != jsp.MissionState.RECORDED:
            self.status.replay.state = jsp.ReplayState.DNE
        elif speed == 0.0:
            self.status.replay.state = jsp.ReplayState.PAUSED
            self.replay_input.put(f"speed {speed}")
        else:
            self.status.replay.state = jsp.ReplayState.PLAYING
            self.replay_input.put(f"speed {speed}")

    def stop_replay(self) -> None:
        """Stops the replay."""

        logger.info("REPLAY STOP")

        if self.replay is not None:
            self.replay.terminate()
        self.replay = None

        # Empty replay output
        self.replay_output: Queue[tuple[int, int, str]] = mp.Queue()  # type:ignore
        self.reset_data()

    def play_mission(self, mission_name: str | None) -> None:
        """Plays the desired mission recording."""

        # Ensure not doing anything silly
        if self.status.mission.recording:
            raise AlreadyRecordingError

        if mission_name is None:
            raise ReplayPlaybackError

        mission_file = mission_path(mission_name, self.missions_dir)
        if mission_file not in self.status.replay.mission_files_list:
            raise MissionNotFoundError(mission_name)

        # Set output data to current mission
        self.status.mission.name = mission_name

        try:
            self.status.mission.epoch = [
                mission.epoch for mission in self.status.replay.mission_list if mission.name == mission_name
            ][0]
        except IndexError:
            self.status.mission.epoch = -1

        # We are not to record when replaying missions
        self.status.mission.state = jsp.MissionState.RECORDED
        self.status.mission.recording = False

        # Replay system
        if self.replay is None:
            # TEMPORARY VERSION CHECK
            replay_ver = 1 if self.status.mission.epoch == -1 else 0

            self.replay = Process(
                target=TelemetryReplay,
                args=(self.replay_output, self.replay_input, self.status.replay.speed, mission_file, replay_ver),
            )
            self.replay.start()

        self.set_replay_speed(
            speed=self.status.replay.last_played_speed if self.status.replay.last_played_speed > 0 else 1
        )

        logger.info(f"REPLAY {mission_name} PLAYING")

    def start_recording(self, mission_name: str | None = None) -> None:
        """Starts recording the current mission. If no mission name is given, the recording epoch is used."""

        # Do not record if already recording or if replay is active
        if self.status.mission.recording:
            raise AlreadyRecordingError

        if self.status.replay.state != jsp.ReplayState.DNE:
            raise ReplayPlaybackError

        logger.info("RECORDING START")

        # Mission Name
        recording_epoch = int(time())
        mission_name = str(recording_epoch) if not mission_name else mission_name
        self.mission_path = get_filepath_for_proposed_name(mission_name, self.missions_dir)
        self.mission_recording_file = open(self.mission_path, "wb")

        # Create SuperBlock in file
        flight = Flight(first_block=1, num_blocks=0, timestamp=recording_epoch)
        self.mission_recording_sb.flights = [flight]
        _ = self.mission_recording_file.write(self.mission_recording_sb.to_bytes())
        self.mission_recording_file.flush()

        # Status update
        self.status.mission.name = mission_name
        self.status.mission.epoch = recording_epoch
        self.status.mission.recording = True

    def stop_recording(self) -> None:
        """Stops the current recording."""

        logger.info("RECORDING STOP")

        if self.mission_recording_file is None:
            raise ValueError("mission_recording_file attribute not initialized to a file.")

        # Flush buffer and close off file
        self.recording_write_bytes(len(self.mission_recording_buffer), spacer=True)
        self.mission_recording_file.flush()
        self.mission_recording_file.close()

        # Reset recording data
        self.mission_recording_file = None
        self.mission_recording_sb = SuperBlock()
        self.mission_recording_buffer = bytearray(b"")

        # Reset mission data except state and last mission time
        self.status.mission = jsp.MissionData(
            state=self.status.mission.state, last_mission_time=self.status.mission.last_mission_time
        )

    def recording_write_bytes(self, num_bytes: int, spacer: bool = False) -> None:
        """Outputs the specified number of bytes from the buffer to the recording file"""

        # If the file is open
        if self.mission_recording_file is None:
            return

        # If there's nothing in buffer
        # Then there's no need to dump buffer
        if num_bytes == 0:
            return

        # Update Superblock with new block count
        self.mission_recording_sb.flights[0].num_blocks += int(math.ceil(num_bytes / 512))
        _ = self.mission_recording_file.seek(0)
        _ = self.mission_recording_file.write(self.mission_recording_sb.to_bytes())

        # Dump entire buffer to file
        blocks = self.mission_recording_buffer[:num_bytes]
        self.mission_recording_buffer = self.mission_recording_buffer[num_bytes:]
        _ = self.mission_recording_file.seek(0, 2)
        _ = self.mission_recording_file.write(blocks)

        # If less than 512 bytes, or a spacer is requested then write a spacer
        if num_bytes < 512 or spacer:
            spacer_block = LoggingMetadataSpacerBlock(512 - (num_bytes % 512))
            _ = self.mission_recording_file.write(spacer_block.to_bytes())

    def process_transmission(self, data: str) -> None:
        """Processes the incoming radio transmission data."""
        # Parse the transmission
        parsed_transmission = parse_rn2483_transmission(data, self.config)
        for block in parsed_transmission.blocks:
            self.update(block)

            # TODO UPDATE FOR V1
            # Write data to file when recording
            # if self.status.mission.recording:
            #     logger.debug(f"Recording: {self.status.mission.recording}")
            #     self.mission_recording_buffer += TelemetryDataBlock(block.subtype, data=block).to_bytes()
            #     if len(self.mission_recording_buffer) >= 512:
            #         buffer_length = len(self.mission_recording_buffer)
            #         self.recording_write_bytes(buffer_length - (buffer_length % 512))

    def update(self, parsed_data: ParsedBlock) -> None:
        """Updates the telemetry buffer with the latest block data and latest mission time."""
        if parsed_data.block_contents.mission_time > self.status.mission.last_mission_time:
            self.status.mission.last_mission_time = parsed_data.block_contents.mission_time

        if self.telemetry.get(parsed_data.block_name) is None:
            self.telemetry[parsed_data.block_name] = [dict(parsed_data.block_contents)]
        else:
            self.telemetry[parsed_data.block_name].append(dict(parsed_data.block_contents))
            if len(self.telemetry[parsed_data.block_name]) > self.config.telemetry_buffer_size:
                self.telemetry[parsed_data.block_name].pop(0)
