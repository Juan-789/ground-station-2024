from __future__ import annotations

"""Contains packet data classes for different payloads that can be received from the rocket."""
# Authors: Arsalan, Matteo Golin

# Imports
import struct
import modules.misc.converter as converter

# Conversion tables
hex_bin_dic = {
    '0': '0000',
    '1': '0001',
    '2': '0010',
    '3': '0011',
    '4': '0100',
    '5': '0101',
    '6': '0110',
    '7': '0111',
    '8': '1000',
    '9': '1001',
    'A': '1010',
    'B': '1011',
    'C': '1100',
    'D': '1101',
    'E': '1110',
    'F': '1111',
    'a': '1010',
    'b': '1011',
    'c': '1100',
    'd': '1101',
    'e': '1110',
    'f': '1111'
}
bin_hex_dic = {v: k for k, v in hex_bin_dic.items()}
kx134_1211_dic = {
    '0x0': 0.781,
    '0x1': 1.563,
    '0x2': 3.125,
    '0x3': 6.25,
    '0x4': 12.5,
    '0x5': 25,
    '0x6': 50,
    '0x7': 100,
    '0x8': 200,
    '0x9': 400,
    '0xA': 800,
    '0xB': 1600,
    '0xC': 3200,
    '0xD': 6400,
    '0xE': 12800,
    '0xF': 25600,
    '0xa': 800,
    '0xb': 1600,
    '0xc': 3200,
    '0xd': 6400,
    '0xe': 12800,
    '0xf': 25600,
}


# Conversion functions
def hex_str_to_int(hex_string: str) -> int:
    """Returns the unsigned integer value of a hexadecimal string."""

    #return int(hex_string, 16)
    return struct.unpack("<I", bytes.fromhex(hex_string))[0]


def bin_to_hex(bin_string: str) -> hex:
    """Returns a hexadecimal code for a given binary string."""

    return hex(int(bin_string, 2))


def hex_to_bin(hex_string: str) -> str:
    """Returns a binary string from a hexadecimal string.

    It is better to use this method than the built-in 'bin()' method because this method will preserve the number of
    bits. For example bin(0x10) will produce 0b'10000 when we actually want 0b'00010000."""

    # Removes '0x' from start of string, if it's present
    if hex_string[0:2] == '0x':
        hex_string = hex_string[2:]

    converted_string = ""
    for char in hex_string:
        converted_string += hex_bin_dic[char]

    return converted_string


def signed_hex_str_to_int(hex_string: str) -> int:
    """Returns an integer value for a given signed hexadecimal string. Return value preserves the number of bits."""

    return struct.unpack("<i", bytes.fromhex(hex_string))[0]
    #bin_input = hex_to_bin(hex_string)

    #if bin_input[0] == '1':
        #return int(bin_input[1:], 2) - (2 ** (len(bin_input) - 1))
    #else:
        #return int(bin_input[1:], 2)


def signed_bin_str_to_int(bin_string: str) -> int:
    """Returns an integer value for a signed binary string."""

    return signed_hex_str_to_int(hex(int(bin_string, 2)))


# Packet classes
def convert_raw(raw_data: str, hex_length: int, signed: bool = False) -> int:
    """Converts a hexadecimal string to an integer."""

    # Value error if string is not the right length
    if len(raw_data) != hex_length:
        raise ValueError(f"Hexadecimal string must be of length {hex_length}.")

    if signed:
        return signed_hex_str_to_int(raw_data)

    return hex_str_to_int(raw_data)


class AltitudeData:

    def __init__(self):
        self._time: int = 0
        self._pressure: int = 0
        self._temperature: int = 0
        self._altitude: int = 0

    # Creation
    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 8) -> AltitudeData:

        """Returns an AltitudeData packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = AltitudeData()

        # Set attributes from raw data
        packet.time = raw_data[:8]
        packet.pressure = raw_data[8:16]
        packet.temperature = raw_data[16:24]
        packet.altitude = raw_data[24:32]

        return packet

    # Getters
    @property
    def time(self) -> int:
        return self._time

    @property
    def pressure(self) -> int:
        return self._pressure

    @property
    def temperature(self) -> int:
        return self._temperature

    @property
    def altitude(self) -> int:
        return self._altitude

    # Setters
    @time.setter
    def time(self, raw_time: str) -> None:

        """Mission time in milliseconds."""

        self._time = convert_raw(raw_time, hex_length=8)

    @pressure.setter
    def pressure(self, raw_pressure: str) -> None:

        """Pressure in kilopascals is converted to Pascals. Signed 32-bit integer in 2's compliment."""

        self._pressure = convert_raw(raw_pressure, hex_length=8, signed=True) / 1000

    @temperature.setter
    def temperature(self, raw_temperature: str) -> None:

        """
        Temperature in millidegrees Celsius/LSB is converted to degrees Celsius. Signed 32-bit integer in 2's
        compliment.
        """

        self._temperature = convert_raw(raw_temperature, hex_length=8, signed=True) / 1000

    @altitude.setter
    def altitude(self, raw_altitude: str) -> None:

        """Altitude in millimeters/LSB is converted to meters. Signed 32-bit integer in 2's compliment."""

        self._altitude = convert_raw(raw_altitude, hex_length=8, signed=True) / 1000

    # Representations
    def __str__(self):
        return f"time:{self.time}, pressure:{self.pressure}, temperature:{self.temperature}, altitude:{self.altitude}\n"

    def __dict__(self):
        return {
            "mission_time": {
                "ms": self._time,
            },
            "pressure": {
                "kpa": self._pressure,
            },
            "temperature": {
                "c": self._temperature,
                "f": converter.celsius_to_fahrenheit(self._temperature),
            },
            "altitude": {
                "m": self._altitude,
            },
        }


class AccelerationData:

    def __init__(self, resolution: int):
        self.resolution: int = resolution  # Resolution for calculations

        self._time: int = 0
        self._fsr: int = 0
        self._x_axis: int = 0
        self._y_axis: int = 0
        self._z_axis: int = 0

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 4) -> AccelerationData:

        """Returns an AccelerationData packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = AccelerationData(resolution)

        # Set attributes from raw data
        packet.time = raw_data[:8]
        packet.fsr = raw_data[8:12]  # Must be set before axes, as they depend on this value
        packet.x_axis = raw_data[12:16]
        packet.y_axis = raw_data[16:20]
        packet.z_axis = raw_data[20:24]

        return packet

    # Getters
    @property
    def time(self) -> int:
        return self._time

    @property
    def fsr(self) -> int:
        return self._fsr

    @property
    def x_axis(self) -> int:
        return self._x_axis

    @property
    def y_axis(self) -> int:
        return self._y_axis

    @property
    def z_axis(self) -> int:
        return self._z_axis

    # Setters
    @time.setter
    def time(self, raw_time: str) -> None:

        """Mission time in milliseconds."""

        self._time = convert_raw(raw_time, hex_length=8)

    @fsr.setter
    def fsr(self, raw_fsr: str) -> None:

        """Adjusts the full scale range based on the resolution."""

        adjustment_factor = 16 - self.resolution + 1
        unadjusted_fsr = convert_raw(raw_fsr, hex_length=4)

        self._fsr = unadjusted_fsr // 2 ** adjustment_factor

    # TODO: These are signed values and so must be fixed
    # If the resolution of the accelerometer is less than 16 bits the values must be sign extended
    @x_axis.setter
    def x_axis(self, raw_x_axis) -> None:

        """X acceleration in meters per second squared. Signed integer in 2's compliment."""

        self._x_axis = convert_raw(raw_x_axis, hex_length=4, signed=True) * self.fsr / 2 ** 15

    @y_axis.setter
    def y_axis(self, raw_y_axis) -> None:

        """Y acceleration in meters per second squared. Signed integer in 2's compliment."""

        self._y_axis = convert_raw(raw_y_axis, hex_length=4, signed=True) * self.fsr / 2 ** 15

    @z_axis.setter
    def z_axis(self, raw_z_axis) -> None:

        """Z acceleration in meters per second squared. Signed integer in 2's compliment."""

        self._z_axis = convert_raw(raw_z_axis, hex_length=4, signed=True) * self.fsr / 2 ** 15

    # Representations
    def __str__(self):
        return f"{self.time}\n" \
               f"{self.fsr}\n" \
               f"{self.x_axis}\n" \
               f"{self.y_axis}\n" \
               f"{self.z_axis}\n"

    def __dict__(self):
        return {
            "mission_time": {
                "ms": self._time,
            },
            "fsr": self._fsr,
            "x_axis": {
                "mps": self._x_axis,
            },
            "y_axis": {
                "mps": self._y_axis,
            },
            "z_axis": {
                "mps": self._z_axis,
            },
        }


class AngularVelocityData:

    def __init__(self, resolution):
        self.resolution = resolution

        self._time: int = 0
        self._fsr: int = 0
        self._x_velocity: int = 0
        self._y_velocity: int = 0
        self._z_velocity: int = 0

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int) -> AngularVelocityData:
        """Returns an AngularVelocityData packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = AngularVelocityData(resolution)

        # Set attributes from raw data
        packet.time = raw_data[:8]
        packet.fsr = raw_data[8:12]  # Must be set before velocities, as they depend on this value
        packet.x_axis = raw_data[12:16]
        packet.y_axis = raw_data[16:20]
        packet.z_axis = raw_data[20:24]

        return packet

    # Getters
    @property
    def time(self) -> int:
        return self._time

    @property
    def fsr(self) -> int:
        return self._fsr

    @property
    def x_velocity(self) -> int:
        return self._x_velocity

    @property
    def y_velocity(self) -> int:
        return self._y_velocity

    @property
    def z_velocity(self) -> int:
        return self._z_velocity

    # Setters
    @time.setter
    def time(self, raw_time: str) -> None:

        """Mission time in milliseconds."""

        self._time = convert_raw(raw_time, hex_length=8)

    @fsr.setter
    def fsr(self, raw_fsr: str) -> None:

        """Adjusts the full scale range based on the resolution."""

        adjustment_factor = 16 - self.resolution + 1
        unadjusted_fsr = convert_raw(raw_fsr, hex_length=4)

        self._fsr = unadjusted_fsr // 2 ** adjustment_factor

    @x_velocity.setter
    def x_velocity(self, raw_x_velocity: str) -> None:

        """X-axis velocity in meters per second. Signed integer in 2's compliment."""

        self._x_velocity = convert_raw(raw_x_velocity, hex_length=4) * self.fsr / 2 ** 15

    @y_velocity.setter
    def y_velocity(self, raw_y_velocity: str) -> None:

        """Y-axis velocity in meters per second. Signed integer in 2's compliment."""

        self._y_velocity = convert_raw(raw_y_velocity, hex_length=4) * self.fsr / 2 ** 15

    @z_velocity.setter
    def z_velocity(self, raw_z_velocity: str) -> None:

        """Z-axis velocity in meters per second. Signed integer in 2's compliment."""

        self._z_velocity = convert_raw(raw_z_velocity, hex_length=4) * self.fsr / 2 ** 15

    # Representations
    def __str__(self):
        return f"fsr: {self.fsr}\n" \
               f"x_velocity: {self.x_velocity}\n" \
               f"y_velocity: {self.y_velocity}\n" \
               f"z_velocity: {self.z_velocity}\n"

    def __dict__(self):
        return {
            "time": {
                "ms": self._time,
            },
            "fsr": self._fsr,
            "x_velocity": {
                "mps": self._x_velocity,
            },
            "y_velocity": {
                "mps": self._y_velocity,
            },
            "z_velocity": {
                "mps": self._z_velocity,
            },
        }


class GNSSMetaDataInfo:

    """Stores metadata on satellites used in the GNSS."""

    def __init__(self):
        self._elevation: int = 0  # Elevation of GNSS satellite in degrees
        self._snr: int = 0  # Signal to noise ratio in dB Hz
        self._id: int = 0  # The pseudo-random noise sequence for GPS satellites or the ID for GLONASS satellites
        self._azimuth: int = 0  # Satellite's azimuth in degrees
        self._satellite_type: str = ""  # The type of satellite (GPS or GLONASS)

    @classmethod
    def create_from_raw(cls, raw_data: str) -> GNSSMetaDataInfo:

        """Returns an GNSSMetaDataInfo packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = GNSSMetaDataInfo()

        # Set attributes from raw data
        packet.elevation = raw_data[0:8]
        packet.SNR = raw_data[8:16]
        packet.id_ = raw_data[16:21]
        packet.azimuth = raw_data[21:30]
        packet.type = raw_data[31]

        return packet

    # Getters
    @property
    def elevation(self) -> int:
        return self._elevation

    @property
    def snr(self) -> int:
        return self._snr

    @property
    def id_(self) -> int:
        return self._id

    @property
    def azimuth(self) -> int:
        return self._azimuth

    @property
    def satellite_type(self) -> str:
        return self._satellite_type

    # Setters
    @elevation.setter
    def elevation(self, raw_elevation) -> None:

        """Elevation of GNSS satellite in degrees."""

        self._elevation = int(raw_elevation, 2)

    @snr.setter
    def snr(self, raw_snr) -> None:

        """Signal to noise ratio in dB Hz."""

        self._snr = int(raw_snr, 2)

    @id_.setter
    def id_(self, raw_id) -> None:

        """The pseudo-random noise sequence for GPS satellites or the satellite ID for GLONASS satellites."""

        self._id = int(raw_id, 2)

    @azimuth.setter
    def azimuth(self, raw_azimuth) -> None:

        """The satellite azimuth in degrees."""

        self._azimuth = int(raw_azimuth, 2)

    @satellite_type.setter
    def satellite_type(self, raw_type: str) -> None:

        """Type of satellite (GPS: 0, GLONASS: 1)."""

        if raw_type == "1":
            self._satellite_type = "GLONASS"
        else:
            self._satellite_type = "GPS"

    # Representations
    def __str__(self):
        return f"elevation: {self._elevation}\n" \
               f"SNR: {self._snr}\n" \
               f"ID: {self._id}\n" \
               f"Azimuth: {self._azimuth}\n" \
               f"type: {self._satellite_type}\n"

    def __dict__(self):
        return {
            "elevation": {
                "deg": self._elevation,
            },
            "snr": {
                "dbhz": self._snr,
            },
            "id": self._id,
            "azimuth": {
                "deg": self._azimuth,
            },
            "satellite_type": self._satellite_type
        }


class GNSSMetaData:

    def __init__(self):
        self._mission_time: int = 0
        self._gps_satellites_in_use: list[int] = []
        self._glonass_satellites_in_use: list[int] = []
        self._satellite_info: dict[int, GNSSMetaDataInfo] = {}

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 8) -> GNSSMetaData:

        """Returns an GNSSMetaData packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = GNSSMetaData()
        binary_raw = bin(int(raw_data, 16))

        # Set attributes from raw data
        packet.mission_time = raw_data[0:8]
        packet.gps_satellites_in_use = binary_raw[34:66]
        packet.glonass_satellites_in_use = binary_raw[66:98]
        packet.satellite_info = binary_raw[98:]

        return packet

    # Getters
    @property
    def mission_time(self) -> int:
        return self._mission_time

    @property
    def gps_satellites_in_use(self) -> list[int]:
        return self._gps_satellites_in_use

    @property
    def glonass_satellites_in_use(self) -> list[int]:
        return self._glonass_satellites_in_use

    @property
    def satellite_info(self) -> dict[int, GNSSMetaDataInfo]:
        return self._satellite_info

    # Setters
    @mission_time.setter
    def mission_time(self, raw_mission_time: str) -> None:

        """Mission time in milliseconds."""

        self._mission_time = convert_raw(raw_mission_time, hex_length=8)

    @gps_satellites_in_use.setter
    def gps_satellites_in_use(self, raw_gps_satellites: bin) -> None:

        """
        Indicates which GPS satellites are used in the current fix. Each bit position represents a GPS pseudo-random
        noise sequence.
        """

        self._gps_satellites_in_use = []
        for _ in range(32):
            if raw_gps_satellites[_] == "1":  # Append GPS satellite IDs if they are in use
                self._gps_satellites_in_use.append(_ + 1)

    @glonass_satellites_in_use.setter
    def glonass_satellites_in_use(self, raw_glonass_satellites: bin) -> None:

        """
        Indicates which GLONASS satellites are used in the current fix.
        Each bit position represents a slot number, starting at bit 0 representing slot 65.
        """

        self._glonass_satellites_in_use = []
        for _ in range(32):
            if raw_glonass_satellites[_] == "1":  # Append IDs of GLONASS satellites in use
                self._glonass_satellites_in_use.append(_ + 1)

    @satellite_info.setter
    def satellite_info(self, raw_satellite_info: bin) -> None:

        """Associates each satellite ID with its metadata."""

        self.satellite_info = {}  # Start with a fresh dictionary
        num_satellites = len(raw_satellite_info) // 32  # Determine the number of satellites

        for _ in range(num_satellites):
            # Create a metadata packet using a 32 bit snippet from the raw_satellite info
            meta_data = GNSSMetaDataInfo.create_from_raw(raw_satellite_info[_ * 32: _ * 32 + 32])
            self.satellite_info[meta_data.id_] = meta_data  # Store metadata in dictionary using the ID as a key

    # Representations
    def __dict__(self):
        return {
            "mission_time": {
                "ms": self._mission_time,
            },
            "gps_sats_in_use": self._gps_satellites_in_use,
            "glonass_sats_in_use": self._glonass_satellites_in_use,
            "satellite_info": self._satellite_info,
        }


class GNSSLocationData:

    def __init__(self):
        self._fix_time: int = 0  # Mission time when fix was received
        self._latitude: int = 0  # Latitude in units of 100 micro arcminute, or 10^-4 arc minutes per LSB
        self._longitude: int = 0  # Longitude in units of 100 micro arcminute, or 10^-4 arc minutes per LSB
        self._utc_time: int = 0  # The time (in UTX) when the fix was received in seconds since the Unix apoch
        self._altitude: int = 0  # Millimeters above sea level
        self._rocket_speed: int = 0  # Speed of the rocket over the ground in units of 1/100th of a knot
        self._rocket_course: int = 0  # Course of rocket in units of 1/100th of a degree
        self._pdop: int = 0  # Position dilution of precision * 100
        self._hdop: int = 0  # Horizontal dilution of precision * 100
        self._vdop: int = 0  # Vertical dilution of precision * 100
        self._num_satellites: int = 0  # Number of GNSS satellites used to get this fix
        self._fix_type: int = 0  # The type of fix, can be either 'unknown', 'not available', '2D fix', or '3D fix'

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 8) -> GNSSLocationData:

        """Returns an GNSSLocationData packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = GNSSLocationData()

        # Set attributes from raw data
        packet.fix_time = raw_data[:8]
        packet.latitude = raw_data[8:16]
        packet.longitude = raw_data[16:24]
        packet.utc_time = raw_data[24:32]
        packet.altitude = raw_data[32:40]
        packet.rocket_speed = raw_data[40:44]
        packet.rocket_course = raw_data[44:48]
        packet.pdop = raw_data[48:52]
        packet.hdop = raw_data[52:56]
        packet.vdop = raw_data[56:60]
        packet._num_satellites = raw_data[60:62]
        packet.fix_type = raw_data[62:]

        return packet

    # Getters
    @property
    def fix_time(self) -> int:
        return self._fix_time

    @property
    def latitude(self) -> int:
        return self._latitude

    @property
    def longitude(self) -> int:
        return self._longitude

    @property
    def utc_time(self) -> int:
        return self._utc_time

    @property
    def altitude(self) -> int:
        return self._altitude

    @property
    def rocket_speed(self) -> int:
        return self._rocket_speed

    @property
    def rocket_course(self) -> int:
        return self._rocket_course

    @property
    def pdop(self) -> int:
        return self._pdop

    @property
    def hdop(self) -> int:
        return self._hdop

    @property
    def vdop(self) -> int:
        return self._vdop

    @property
    def num_satellites(self) -> int:
        return self._num_satellites

    @property
    def fix_type(self) -> int:
        return self._fix_type

    # Setters
    @fix_time.setter
    def fix_time(self, raw_fix_time: str) -> None:

        """Mission time in milliseconds."""

        self._fix_time = convert_raw(raw_fix_time, hex_length=8)

    @latitude.setter
    def latitude(self, raw_latitude: str) -> None:

        """Latitude in units of 100 micro-arcminutes per LSB. Signed 32-bit integer in 2's compliment."""

        self._latitude = convert_raw(raw_latitude, hex_length=8, signed=True)

    @longitude.setter
    def longitude(self, raw_longitude: str) -> None:

        """Longitude in 100 micro-arcminutes per LSB. Signed 32-bit integer in 2's compliment."""

        self._longitude = convert_raw(raw_longitude, hex_length=8, signed=True)

    @utc_time.setter
    def utc_time(self, raw_utc_time) -> None:

        """UTC time when fix was received in seconds since Unix epoch."""

        self._utc_time = convert_raw(raw_utc_time, hex_length=8)

    @altitude.setter
    def altitude(self, raw_altitude: str) -> None:

        """Altitude in millimeters above sea level. Signed 32-bit integer in 2's compliment."""

        self._altitude = convert_raw(raw_altitude, hex_length=8)

    @rocket_speed.setter
    def rocket_speed(self, raw_rocket_speed: str) -> None:

        """Speed over ground in hundredths of a knot. Signed 16-bit integer in 2's compliment."""

        self._rocket_speed = convert_raw(raw_rocket_speed, hex_length=4, signed=True)

    @rocket_course.setter
    def rocket_course(self, raw_rocket_course: str) -> None:

        """Course over ground in hundredths of a degree. Signed 16-bit integer in 2's compliment."""

        self._rocket_course = convert_raw(raw_rocket_course, hex_length=4, signed=True)

    @pdop.setter
    def pdop(self, raw_pdop: str) -> None:

        """Position dilution of precision multiplied by 100."""

        self._pdop = convert_raw(raw_pdop, hex_length=4)

    @hdop.setter
    def hdop(self, raw_hdop: str) -> None:

        """Horizontal dilution of precision multiplied by 100."""

        self._hdop = convert_raw(raw_hdop, hex_length=4)

    @vdop.setter
    def vdop(self, raw_vdop: str) -> None:

        """Vertical dilution of precision multiplied by 100."""

        self._vdop = convert_raw(raw_vdop, hex_length=4)

    @num_satellites.setter
    def num_satellites(self, raw_num_satellites) -> None:

        """Number of GNSS satellites used."""

        self._num_satellites = convert_raw(raw_num_satellites, hex_length=2)

    @fix_type.setter
    def fix_type(self, raw_fix_type: str) -> None:

        """Type of the fix."""

        # Convert type to integer
        fix_type_int = int(hex_to_bin(raw_fix_type)[2:4], 2)

        fix_type = "error"  # Assume error by default
        match fix_type_int:
            case 0:
                fix_type = "unknown"
            case 1:
                fix_type = "not available"
            case 2:
                fix_type = "2D fix"
            case 3:
                fix_type = "3D"

        self._fix_type = fix_type

    # Representations
    def __str__(self):
        return f"fix time: {self.fix_time}\n" \
               f"latitude: {self.latitude}\n" \
               f"longitude: {self.longitude}\n" \
               f"utc_time: {self.utc_time}\n" \
               f"altitude: {self.altitude}\n" \
               f"rocket speed: {self.rocket_speed}\n" \
               f"rocket_course: {self.rocket_course}\n" \
               f"pdop: {self.pdop}\n" \
               f"hdop: {self.hdop}\n" \
               f"vdop: {self.vdop}\n" \
               f"num_sats: {self.num_satellites}\n" \
               f"fix_type: {self.fix_type}\n"

    def __dict__(self):
        return {
            "mission_time": {
                "ms": self._fix_time,
            },
            "coords": {
                "latitude": {
                    "cent_micro_arcmins": self._latitude,
                },
                "longitude": {
                    "cent_micro_armins": self._longitude,
                },
            },
            "utc_time": self._utc_time,
            "altitude": {
                "mm": self._altitude,
            },
            "speed": {
                "cent_knot": self._rocket_speed,
            },
            "course": {
                "cent_knot": self._rocket_course,
            },
            "pdop": self._pdop,
            "hdop": self._hdop,
            "vdop": self._vdop,
            "num_sats": self._num_satellites,
            "fix_type": self._fix_type,
        }


class MPU9250MeasurementData:
    """Measurement data from the MPU9250 IMU."""

    def __init__(self, raw_bin):
        self.time_stamp: int = int(raw_bin[0:32], 2)
        self.accel_x: int = int(raw_bin[32:48], 2)
        self.accel_y: int = int(raw_bin[48:64], 2)
        self.accel_z: int = int(raw_bin[64:80], 2)
        self.temperature: int = int(raw_bin[80:96], 2)

        self.gyro_x: int = int(raw_bin[96:112], 2)
        self.gyro_y: int = int(raw_bin[112:128], 2)
        self.gyro_z: int = int(raw_bin[128:144], 2)

        self.mag_x: int = int(raw_bin[144:160], 2)
        self.mag_y: int = int(raw_bin[160:176], 2)
        self.mag_z: int = int(raw_bin[176:192], 2)

        self.mag_valid: int = int(raw_bin[195], 2)
        self.mag_resolution: int = int(raw_bin[196], 2)

    # Representations
    def __str__(self):
        return f"time: {self.time_stamp}\n" \
               f"temperature: {self.temperature}\n" \
               f"accel x: {self.accel_x}\n" \
               f"accel y: {self.accel_y}\n" \
               f"accel z: {self.accel_z}\n" \
               f"gyro x: {self.gyro_x}\n" \
               f"gyro y: {self.gyro_y}\n" \
               f"gyro z: {self.gyro_z}\n" \
               f"mag x: {self.mag_x}\n" \
               f"mag y: {self.mag_y}\n" \
               f"mag z: {self.mag_z}\n" \
               f"mag valid: {self.mag_valid}\n" \
               f"mag resolution: {self.mag_resolution}\n"

    def __dict__(self):
        return {}


class MPU9250Data:

    """Data from the MPU9250 IMU."""

    def __init__(self):
        self._time: int = 0
        self._ag_sample_rate: int = 0  # Sample rate of the accelerometer and gyroscope
        self._accelerometer_fsr: int = 0  # Accelerometer full scale range
        self._gyroscope_fsr: int = 0  # Gyroscope full scale range
        self._accelerometer_bw: int = 0  # Bandwidth for the low pass filter used by the accelerometer
        self._gyroscope_bw: int = 0  # Bandwidth for the low pass filter used by the gyroscope

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 8) -> MPU9250Data:
        """Returns an MPU9250Data packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = MPU9250Data()
        raw_binary = hex_to_bin(raw_data)

        # Set attributes from raw data
        packet.time = raw_data[:8]
        packet.ag_sample_rate = raw_data[8:10]
        packet.accelerometer_fsr = raw_binary[39:41]
        packet.gyroscope_fsr = None
        packet.accelerometer_bw = None
        packet.gyroscope_bw = None

        return packet

    # Getters
    @property
    def time(self) -> int:
        return self._time

    @property
    def ag_sample_rate(self) -> int:
        return self._ag_sample_rate

    @property
    def accelerometer_fsr(self) -> int:
        return self._accelerometer_fsr

    @property
    def gyroscope_fsr(self) -> int:
        return self._gyroscope_fsr

    @property
    def accelerometer_bw(self) -> int:
        return self._accelerometer_bw

    @property
    def gyroscope_bw(self) -> int:
        return self._gyroscope_bw

    # Setters
    @time.setter
    def time(self, raw_time: str) -> None:

        """Mission time in milliseconds."""

        self._time = convert_raw(raw_time, hex_length=8)

    @ag_sample_rate.setter
    def ag_sample_rate(self, raw_ag_sample: str) -> None:

        """Sample rate of accelerometer and gyroscope."""

        self._ag_sample_rate = convert_raw(raw_ag_sample, hex_length=2)

    @accelerometer_fsr.setter
    def accelerometer_fsr(self, raw_acc_fsr: bin) -> None:

        """Full scale range for the accelerometer."""

        self._accelerometer_fsr = 2 ** (int(raw_acc_fsr, 2) + 1)

    # TODO: The following three setters need to be finished after we receive an input from this device

    @gyroscope_fsr.setter
    def gyroscope_fsr(self, raw_gyro_fsr) -> None:

        """Full scale range for the gyroscope."""

        pass  # TODO

    @gyroscope_bw.setter
    def gyroscope_bw(self, raw_gyro_bw) -> None:

        """Gyroscope low pass filter bandwidth."""

        pass  # TODO

    @accelerometer_bw.setter
    def accelerometer_bw(self, raw_acc_bw) -> None:

        """Accelerometer low pass filter bandwidth."""

        pass  # TODO

    # String representation
    def __str__(self):
        return f"Time: {self.time}\n" \
               f"AG sample rate: {self.ag_sample_rate}\n" \
               f"Accelerometer FSR: {self.accelerometer_fsr}\n" \
               f"Gyroscope FSR: {self.gyroscope_fsr}\n" \
               f"Accelerometer BW: {self.accelerometer_bw}\n" \
               f"Gyroscope BW: {self.gyroscope_bw}"


class KX1341211MeasurementData:

    """Contains measurement data for the KX1341211 packet."""

    def __init__(self):
        self._x_acceleration: int = 0
        self._y_acceleration: int = 0
        self._z_acceleration: int = 0

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 8) -> KX1341211MeasurementData:

        """Returns an KX1341211MeasurementData packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = KX1341211MeasurementData()

        # Set attributes from raw data
        resolution = len(raw_data)

        if resolution == 24:
            packet.x_acceleration = raw_data[:8]
            packet.y_acceleration = raw_data[8:16]
            packet.z_acceleration = raw_data[16:24]
        elif resolution == 48:
            packet.x_acceleration = raw_data[:16]
            packet.y_acceleration = raw_data[16:32]
            packet.z_acceleration = raw_data[32:48]
        else:
            raise ValueError(f"Measurement data only supports 24 or 48 bit resolution, not {resolution} bit.")

        return packet

    # Getters
    @property
    def x_acceleration(self):
        return self._x_acceleration

    @property
    def y_acceleration(self):
        return self._y_acceleration

    @property
    def z_acceleration(self):
        return self._z_acceleration

    # Setters
    @x_acceleration.setter
    def x_acceleration(self, raw_x_accel: str) -> None:

        resolution = len(raw_x_accel)

        if resolution == 8:
            self._x_acceleration = signed_bin_str_to_int(raw_x_accel)
        elif resolution == 16:
            self._x_acceleration = int(raw_x_accel, 2)
        else:
            raise ValueError(f"Acceleration only supports 8 or 16 bit resolution, not {resolution} bit.")

    @y_acceleration.setter
    def y_acceleration(self, raw_y_accel: str) -> None:

        resolution = len(raw_y_accel)

        if resolution == 8:
            self._y_acceleration = signed_bin_str_to_int(raw_y_accel)
        elif resolution == 16:
            self._y_acceleration = int(raw_y_accel, 2)
        else:
            raise ValueError(f"Acceleration only supports 8 or 16 bit resolution, not {resolution} bit.")

    @z_acceleration.setter
    def z_acceleration(self, raw_z_accel: str) -> None:

        resolution = len(raw_z_accel)

        if resolution == 8:
            self._z_acceleration = signed_bin_str_to_int(raw_z_accel)
        elif resolution == 16:
            self._z_acceleration = int(raw_z_accel, 2)
        else:
            raise ValueError(f"Acceleration only supports 8 or 16 bit resolution, not {resolution} bit.")

    # String representation
    def __str__(self):
        return f"x: {self.x_acceleration}\n" \
               f"y: {self.y_acceleration}\n" \
               f"z: {self.z_acceleration}\n"


class KX1341211Data:

    def __init__(self):
        self._time: int = 0
        self._data_rate: int = 0  # Data rate of the accelerometer in Hz
        self._full_scale_range: int = 0  # Set the full scale range in Gs
        self._corner_frequency: int = 0  # The corner frequency of the accelerometer's low pass filter in Hz

        self._resolution: int = 0
        self._padding: int = 0
        self._measurements: list[KX1341211MeasurementData] = []  # The actual measurements taken by the accelerometer

    @classmethod
    def create_from_raw(cls, raw_data: str, resolution: int = 8) -> KX1341211Data:

        """Returns an KX1341211Data packet from raw data."""

        print(f"Packet data being set from {raw_data}")

        packet = KX1341211Data()
        raw_binary = hex_to_bin(raw_data)

        # Set attributes from raw data
        packet.time = raw_binary[:32]
        packet.data_rate = raw_binary[32:36]
        packet.full_scale_range = raw_binary[36:38]
        packet.corner_frequency = raw_binary[38]

        packet.resolution = raw_binary[39]
        packet.padding = raw_binary[46:48]
        packet.measurements = raw_binary[48:]

        return packet

    # Getters
    @property
    def time(self) -> int:
        return self._time

    @property
    def data_rate(self) -> int:
        return self._data_rate

    @property
    def full_scale_range(self) -> int:
        return self._full_scale_range

    @property
    def corner_frequency(self) -> int:
        return self._corner_frequency

    @property
    def measurements(self) -> list[KX1341211MeasurementData]:
        return self._measurements

    @property
    def resolution(self) -> int:
        return self._resolution

    @property
    def padding(self) -> int:
        return self._padding

    # Setters
    @time.setter
    def time(self, raw_time: bin) -> None:

        """Mission time in milliseconds."""

        self._time = int(raw_time, 2)

    @data_rate.setter
    def data_rate(self, raw_data_rate: bin) -> None:

        """Output data rate of the accelerometer."""

        self._data_rate = kx134_1211_dic[hex(int(raw_data_rate, 2))]

    @full_scale_range.setter
    def full_scale_range(self, raw_range: bin) -> None:

        """Full scale range of the accelerometer."""

        range_type = int(raw_range, 2)  # Can be 0 - 3

        if range_type <= 3:
            full_scale_range = 2 ** (range_type + 3)

        # Invalid range
        else:
            full_scale_range = -1

        self._full_scale_range = full_scale_range

    @corner_frequency.setter
    def corner_frequency(self, raw_corner_freq: bin) -> None:

        """The corner frequency of the accelerometer's low pass filter in Hz."""

        if raw_corner_freq == "0":
            self._corner_frequency = self._data_rate / 9
        else:
            self._corner_frequency = self._data_rate / 2

    @resolution.setter
    def resolution(self, raw_resolution: bin) -> None:

        """Output resolution for the accelerometer."""

        if raw_resolution == '0':
            self._resolution = 8
        else:
            self._resolution = 16

    @padding.setter
    def padding(self, raw_padding: bin) -> None:

        """Number of padding bytes present after the end of the acceleration data."""

        self._padding = int(raw_padding, 2) * 8

    @measurements.setter
    def measurements(self, raw_measurements: bin) -> None:

        self._measurements = []  # Start fresh
        chunk_size = self._resolution * 8

        # Split data into readable chunks
        acceleration_data = []
        # From 0 to the end, with a step size of the chunk size
        for _ in range(0, len(raw_measurements) - self.padding, chunk_size):
            acceleration_data.append(raw_measurements[_:_ + chunk_size])

        # Create a Measurement packet for each data chunk
        for data_chunk in acceleration_data:
            self._measurements.append(KX1341211MeasurementData.create_from_raw(data_chunk))

    # String representation
    def __str__(self):

        data_points_str = ''
        for m in self.measurements:
            data_points_str += str(m)
            data_points_str += '____\n'

        return f"time stamp: {self.time}\n" \
               f"data rate: {self.data_rate}\n" \
               f"full scale range: {self.full_scale_range}\n" \
               f"corner frequency: {self.corner_frequency}\n" \
               f"measurements:\n{data_points_str}" + "-" * 20
