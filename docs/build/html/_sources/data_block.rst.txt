data_block.py
-----------------------
.. autoexception:: modules.telemetry.data_block.DataBlockException
.. autoexception:: modules.telemetry.data_block.DataBlockUnknownException
.. autoclass:: modules.telemetry.data_block.DataBlock
    :members: __len__, to_payload, from_payload, parse
.. autoclass:: modules.telemetry.data_block.DebugMessageDataBlock
    :members: __len__, from_payload, to_payload, __str__, __iter__
.. autoclass:: modules.telemetry.data_block.StartupMessageDataBlock
    :members: __len__, from_payload, to_payload, __str__, __iter__
.. autoclass::modules.telemetry.data_block.SensorStatus
    :members: __str__
.. autoclass::modules.telemetry.data_block.SDCardStatus
    :members: __str__
.. autoclass::modules.telemetry.data_block.DeploymentState
    :members: __str__
.. autoclass::modules.telemetry.data_block.StatusDataBlock
    :members:  __len__, from_payload, to_payload, __str__, __iter__
.. autoclass::modules.telemetry.data_block.AltitudeDataBlock
    :members: from_payload, to_payload, __str__, __iter__
.. autoclass::modules.telemetry.data_block.AccelerationDataBlock
    :members: from_payload, to_payload, __str__, __iter__
.. autoclass::modules.telemetry.data_block.AngularVelocityDataBlock
    :members: from_payload, to_payload, __str__, __iter__
.. autoclass::modules.telemetry.data_block.GNSSLocationFixType
.. autoclass::modules.telemetry.data_block.GNSSLocationBlock
    :members: from_payload, to_payload, coord_to_str, __str__, __iter__

