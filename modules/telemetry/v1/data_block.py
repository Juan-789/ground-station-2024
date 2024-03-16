# Contains data block utilities for version 1 of the radio packet format
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Type
from enum import IntEnum
import struct

from modules.misc.converter import metres_to_feet, milli_degrees_to_celsius, pascals_to_psi


class BlockException(Exception):
    pass


class BlockUnknownException(BlockException):
    pass


class DataBlockSubtype(IntEnum):
    """Lists the subtypes of data blocks that can be sent in Version 1 of the packet encoding format."""

    DEBUG_MESSAGE = 0x00
    ALTITUDE = 0x01
    TEMPERATURE = 0x02
    PRESSURE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS_LOCATION = 0x06
    GNSS_METADATA = 0x07
    HUMIDITY = 0x08
    STATUS = 0x09
    RESERVED = 0xFF

    def __str__(self):
        match self:
            case DataBlockSubtype.DEBUG_MESSAGE:
                return "DEBUG MESSAGE"
            case DataBlockSubtype.ALTITUDE:
                return "ALTITUDE"
            case DataBlockSubtype.TEMPERATURE:
                return "TEMPERATURE"
            case DataBlockSubtype.PRESSURE:
                return "PRESSURE"
            case DataBlockSubtype.ACCELERATION:
                return "ACCELERATION"
            case DataBlockSubtype.ANGULAR_VELOCITY:
                return "ANGULAR VELOCITY"
            case DataBlockSubtype.GNSS_LOCATION:
                return "GNSS LOCATION"
            case DataBlockSubtype.GNSS_METADATA:
                return "GNSS METADATA"
            case DataBlockSubtype.HUMIDITY:
                return "HUMIDITY"
            case DataBlockSubtype.STATUS:
                return "STATUS"
            case _:
                return "RESERVED"


class DataBlockException(BlockException):
    pass


class DataBlockUnknownException(BlockUnknownException):
    pass


class DataBlock(ABC):
    """The abstract base interface for all data blocks."""

    def __init__(self, mission_time: int) -> None:
        """Constructs a data block with the given mission time."""
        self.mission_time: int = mission_time

    @classmethod
    @abstractmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a data block from bytes.
        Returns:
            A new data block.
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Get the length of a data block in bytes.
        Returns:
            The length of a data block in bytes, not include the block header.
        """
        pass

    @abstractmethod
    def __str__(self):
        """Returns a string of the data block in a human-readable format"""
        pass

    @abstractmethod
    def __iter__(self):
        """Returns an iterator over the data block, typically used to get dictionaries"""
        pass

    @staticmethod
    def parse(block_subtype: DataBlockSubtype, payload: bytes) -> DataBlock:
        """Unmarshal a bytes object to appropriate block class."""

        SUBTYPE_CLASSES: dict[DataBlockSubtype, Type[DataBlock]] = {
            DataBlockSubtype.DEBUG_MESSAGE: DebugMessageDB,
            DataBlockSubtype.ALTITUDE: AltitudeDB,
            DataBlockSubtype.TEMPERATURE: TemperatureDB,
            DataBlockSubtype.PRESSURE: PressureDB,
            DataBlockSubtype.HUMIDITY: HumidityDB,
            DataBlockSubtype.STATUS: StatusDataBlock,
        }

        subtype = SUBTYPE_CLASSES.get(block_subtype)

        if subtype is None:
            raise DataBlockUnknownException(f"Unknown data block subtype: {block_subtype} {payload} {payload.hex()}")

        return subtype.from_bytes(payload=payload)


class DebugMessageDB(DataBlock):
    """Represents a debug message data block."""

    def __init__(self, mission_time: int, message: str) -> None:
        super().__init__(mission_time)
        self.message: str = message

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a debug message data block from bytes.
        Returns:
            A debug message data block.
        """
        mission_time = struct.unpack("<I", payload[:4])[0]
        message = payload[4:].decode("utf-8")
        return cls(mission_time, message)

    def __len__(self) -> int:
        """
        Get the length of a debug message data block in bytes.
        Returns:
            The length of a debug message data block in bytes, not including the block header.
        """
        return 4 + len(self.message)

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, message: {self.message}"

    def __iter__(self):
        """
        Returns the iterator over the debug message
        """
        yield "mission_time", self.mission_time
        yield "message", self.message


class AltitudeDB(DataBlock):
    """Represents an altitude data block."""

    def __init__(self, mission_time: int, altitude: int) -> None:
        super().__init__(mission_time)
        self.altitude = altitude

    def __len__(self) -> int:
        """
        Get the length of an altitude data block in bytes.
        Returns:
            The length of an altitude data block in bytes, not including the block header.
        """
        return 16

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a data block from bytes.
        Returns:
            An altitude data block.
        """

        parts = struct.unpack("<Ii", payload)
        return cls(parts[0], parts[1] / 1000)  # Altitude is sent in mm

    def to_bytes(self) -> bytes:
        return struct.pack("<Ii", int(self.altitude))

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, altitude: {self.altitude} m"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "altitude", {"metres": self.altitude, "feet": metres_to_feet(self.altitude)}


class TemperatureDB(DataBlock):
    """Represents a temperature data block."""

    def __init__(self, mission_time: int, temperature: int) -> None:
        super().__init__(mission_time)
        self.temperature: int = temperature

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a temperature data block from bytes.
        Returns:
            A temperature data block.
        """
        parts = struct.unpack("<Ii", payload)
        return cls(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a temperature data block in bytes.
        Returns:
            The length of a temperature data block in bytes, not including the block header.
        """
        return 8

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time} ms, "
            f"temperature: {self.temperature} mC "
            f"({round(self.temperature / 1000, 1)}°C)"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "temperature", {"millidegrees": self.temperature, "celsius": milli_degrees_to_celsius(self.temperature)}


class PressureDB(DataBlock):
    """Represents a pressure data block."""

    def __init__(self, mission_time: int, pressure: int) -> None:
        """
        Constructs a pressure data block.

        Args:
            mission_time: The mission time the altitude was measured at in milliseconds since launch.
            pressure: The pressure in millibars.

        """
        super().__init__(mission_time)
        self.pressure: int = pressure

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a pressure data block from bytes.
        Returns:
            A pressure data block.
        """
        parts = struct.unpack("<II", payload)
        return cls(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a pressure data block in bytes.
        Returns:
            The length of a pressure data block in bytes, not including the block header.
        """
        return 8

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, pressure: {self.pressure} Pa"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "pressure", {"pascals": self.pressure, "psi": pascals_to_psi(self.pressure)}


class HumidityDB(DataBlock):
    """Represents a humidity data block."""

    def __init__(self, mission_time: int, humidity: int) -> None:
        """
        Constructs a humidity data block.

        Args:
            mission_time: The mission time the humidity was measured at in milliseconds since launch.
            humidity: The calculated relative humidity in ten thousandths of a percent.

        """
        super().__init__(mission_time)
        self.humidity: int = humidity

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a humidity data block from bytes.
        Returns:
            A humidity data block.
        """
        parts = struct.unpack("<II", payload)
        return cls(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a humidity data block in bytes.
        Returns:
            The length of a humidity data block in bytes, not including the block header.
        """
        return 8

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, humidity: {round(self.humidity / 100)}%"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "percentage", round(self.humidity / 100)

class SensorStatus(IntEnum):
    SENSOR_STATUS_NONE = 0x0
    SENSOR_STATUS_INITIALIZING = 0x1
    SENSOR_STATUS_RUNNING = 0x2
    SENSOR_STATUS_SELF_TEST_FAILED = 0x3
    SENSOR_STATUS_FAILED = 0x4

    def __str__(self):
        return {
            SensorStatus.SENSOR_STATUS_NONE: "none",
            SensorStatus.SENSOR_STATUS_INITIALIZING: "initializing",
            SensorStatus.SENSOR_STATUS_RUNNING: "running",
            SensorStatus.SENSOR_STATUS_SELF_TEST_FAILED: "self test failed",
            SensorStatus.SENSOR_STATUS_FAILED: "failed",
        }.get(self, "unknown")

class SDCardStatus(IntEnum):
    SD_CARD_STATUS_NOT_PRESENT = 0x0
    SD_CARD_STATUS_INITIALIZING = 0x1
    SD_CARD_STATUS_READY = 0x2
    SD_CARD_STATUS_FAILED = 0x3

    def __str__(self):
        return {
            SDCardStatus.SD_CARD_STATUS_NOT_PRESENT: "card not present",
            SDCardStatus.SD_CARD_STATUS_INITIALIZING: "initializing",
            SDCardStatus.SD_CARD_STATUS_READY: "ready",
            SDCardStatus.SD_CARD_STATUS_FAILED: "failed",
        }.get(self, "unknown")


class DeploymentState(IntEnum):
    DEPLOYMENT_STATE_DNE = -1
    DEPLOYMENT_STATE_IDLE = 0x0
    DEPLOYMENT_STATE_ARMED = 0x1
    DEPLOYMENT_STATE_POWERED_ASCENT = 0x2
    DEPLOYMENT_STATE_COASTING_ASCENT = 0x3
    DEPLOYMENT_STATE_DROGUE_DEPLOY = 0x4
    DEPLOYMENT_STATE_DROGUE_DESCENT = 0x5
    DEPLOYMENT_STATE_MAIN_DEPLOY = 0x6
    DEPLOYMENT_STATE_MAIN_DESCENT = 0x7
    DEPLOYMENT_STATE_RECOVERY = 0x8

    def __str__(self):
        return {
            DeploymentState.DEPLOYMENT_STATE_IDLE: "idle",
            DeploymentState.DEPLOYMENT_STATE_ARMED: "armed",
            DeploymentState.DEPLOYMENT_STATE_POWERED_ASCENT: "powered ascent",
            DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT: "coasting ascent",
            DeploymentState.DEPLOYMENT_STATE_DROGUE_DEPLOY: "drogue deployed",
            DeploymentState.DEPLOYMENT_STATE_DROGUE_DESCENT: "drogue descent",
            DeploymentState.DEPLOYMENT_STATE_MAIN_DEPLOY: "main deployed",
            DeploymentState.DEPLOYMENT_STATE_MAIN_DESCENT: "main descent",
            DeploymentState.DEPLOYMENT_STATE_RECOVERY: "recovery",
            DeploymentState.DEPLOYMENT_STATE_DNE: "",
        }.get(self, "unknown")

class StatusDataBlock(DataBlock):
    """Encapsulates the status data."""

    def __init__(
        self,
        mission_time: int,
        kx134_state: SensorStatus,
        alt_state: SensorStatus,
        imu_state: SensorStatus,
        sd_state: SDCardStatus,
        deployment_state: DeploymentState,
        sd_blocks_recorded: int,
        sd_checkouts_missed: int,
    ):
        super().__init__(mission_time)
        self.kx134_state: SensorStatus = kx134_state
        self.alt_state: SensorStatus = alt_state
        self.imu_state: SensorStatus = imu_state
        self.sd_state: SDCardStatus = sd_state
        self.deployment_state: DeploymentState = deployment_state
        self.sd_blocks_recorded: int = sd_blocks_recorded
        self.sd_checkouts_missed: int = sd_checkouts_missed

    def __len__(self) -> int:
        return 16

    @classmethod
    def from_bytes(cls, payload: bytes):
        parts = struct.unpack("<IIII", payload)

        try:
            kx134_state = SensorStatus((parts[1] >> 16) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid KX134 state: {(parts[1] >> 16) & 0x7}") from error

        try:
            alt_state = SensorStatus((parts[1] >> 19) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid altimeter state: {(parts[1] >> 19) & 0x7}") from error

        try:
            imu_state = SensorStatus((parts[1] >> 22) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid IMU state: {(parts[1] >> 22) & 0x7}") from error

        try:
            sd_state = SDCardStatus((parts[1] >> 25) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid SD card state: {(parts[1] >> 25) & 0x7}") from error

        try:
            deployment_state = DeploymentState((parts[1] >> 28) & 0xF)
        except ValueError as error:
            raise DataBlockException(f"Invalid deployment state: {(parts[1] >> 28) & 0xf}") from error

        return StatusDataBlock(
            parts[0], kx134_state, alt_state, imu_state, sd_state, deployment_state, parts[2], parts[3]
        )

    def to_payload(self) -> bytes:
        """Transforms a StatusData block into a byte payload."""
        kx134_state = (self.kx134_state.value & 0x7) << 16
        alt_state = (self.alt_state.value & 0x7) << 19
        imu_state = (self.imu_state.value & 0x7) << 22
        sd_state = (self.sd_state.value & 0x7) << 25
        deployment_state = (self.deployment_state.value & 0x7) << 28

        states = kx134_state | alt_state | imu_state | sd_state | deployment_state

        return struct.pack("<IIII", self.mission_time, states, self.sd_blocks_recorded, self.sd_checkouts_missed)

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time} ms, kx134 state: "
            f"{str(self.kx134_state)}, altimeter state: {str(self.alt_state)}, "
            f"IMU state: {str(self.imu_state)}, SD driver state: {str(self.sd_state)}, "
            f"deployment state: {str(self.deployment_state)}, blocks recorded: "
            f" {self.sd_blocks_recorded}, checkouts missed: {self.sd_checkouts_missed}"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "kx134_state", self.kx134_state
        yield "altimeter_state", self.alt_state
        yield "imu_state", self.imu_state
        yield "sd_driver_state", self.sd_state
        yield "deployment_state", self.deployment_state
        yield "blocks_recorded", self.sd_blocks_recorded
        yield "checkouts_missed", self.sd_checkouts_missed



def parse_data_block(type: DataBlockSubtype, payload: bytes) -> DataBlock:
    """
    Parses a bytes payload into the correct data block type.
    Args:
        type: The type of data block to parse the bytes into.
        payload: The bytes payload to parse into a data block.
    Returns:
        The parse data block.
    Raises:
        ValueError: Raised if the bytes cannot be parsed into the corresponding type.
    """

    match type:
        case DataBlockSubtype.DEBUG_MESSAGE:
            return DebugMessageDB.from_bytes(payload)
        case DataBlockSubtype.ALTITUDE:
            return AltitudeDB.from_bytes(payload)
        case DataBlockSubtype.TEMPERATURE:
            return TemperatureDB.from_bytes(payload)
        case DataBlockSubtype.PRESSURE:
            return PressureDB.from_bytes(payload)
        case DataBlockSubtype.HUMIDITY:
            return HumidityDB.from_bytes(payload)
        case DataBlockSubtype.STATUS:
            return StatusDataBlock.from_bytes(payload)
        case _:
            raise NotImplementedError
