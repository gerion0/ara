/**
 ******************************************************************************
 * @addtogroup UAVObjects OpenPilot UAVObjects
 * @{ 
 * @addtogroup StabilizationDesired StabilizationDesired
 * @brief The desired attitude that @ref StabilizationModule will try and achieve if FlightMode is Stabilized.  Comes from @ref ManaulControlModule.
 *
 * Autogenerated files and functions for StabilizationDesired Object
 * @{ 
 *
 * @file       stabilizationdesired.c
 * @author     The OpenPilot Team, http://www.openpilot.org Copyright (C) 2010-2013.
 * @brief      Implementation of the StabilizationDesired object. This file has been 
 *             automatically generated by the UAVObjectGenerator.
 * 
 * @note       Object definition file: stabilizationdesired.xml. 
 *             This is an automatically generated file.
 *             DO NOT modify manually.
 *
 * @see        The GNU Public License (GPL) Version 3
 *
 *****************************************************************************/
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 * for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */

#include <openpilot.h>
#include "stabilizationdesired.h"

// Private variables
#if (defined(__MACH__) && defined(__APPLE__))
static UAVObjHandle handle __attribute__((section("__DATA,_uavo_handles")));
#else
static UAVObjHandle handle __attribute__((section("_uavo_handles")));
#endif

#if STABILIZATIONDESIRED_ISSETTINGS
SETTINGS_INITCALL(StabilizationDesiredInitialize);
#endif

/**
 * Initialize object.
 * \return 0 Success
 * \return -1 Failure to initialize or -2 for already initialized
 */
int32_t StabilizationDesiredInitialize(void)
{
    // Compile time assertion that the StabilizationDesiredDataPacked and StabilizationDesiredData structs
    // have the same size (though instances of StabilizationDesiredData
    // should be placed in memory by the linker/compiler on a 4 byte alignment).
    PIOS_STATIC_ASSERT(sizeof(StabilizationDesiredDataPacked) == sizeof(StabilizationDesiredData));
    
    // Don't set the handle to null if already registered
    if (UAVObjGetByID(STABILIZATIONDESIRED_OBJID)) {
        return -2;
    }

    static const UAVObjType objType = {
       .id = STABILIZATIONDESIRED_OBJID,
       .instance_size = STABILIZATIONDESIRED_NUMBYTES,
       .init_callback = &StabilizationDesiredSetDefaults,
    };

    // Register object with the object manager
    handle = UAVObjRegister(&objType,
        STABILIZATIONDESIRED_ISSINGLEINST, STABILIZATIONDESIRED_ISSETTINGS, STABILIZATIONDESIRED_ISPRIORITY);

    // Done
    return handle ? 0 : -1;
}

static inline void DataOverrideDefaults(__attribute__((unused)) StabilizationDesiredData * data) {}

void StabilizationDesiredDataOverrideDefaults(StabilizationDesiredData * data) __attribute__((weak, alias("DataOverrideDefaults")));

/**
 * Initialize object fields and metadata with the default values.
 * If a default value is not specified the object fields
 * will be initialized to zero.
 */
void StabilizationDesiredSetDefaults(UAVObjHandle obj, uint16_t instId)
{
    StabilizationDesiredData data;

    // Initialize object fields to their default values
    UAVObjGetInstanceData(obj, instId, &data);
    memset(&data, 0, sizeof(StabilizationDesiredData));

    StabilizationDesiredDataOverrideDefaults(&data);
    UAVObjSetInstanceData(obj, instId, &data);

    // Initialize object metadata to their default values
    if ( instId == 0 ) {
        UAVObjMetadata metadata;
        metadata.flags =
            ACCESS_READWRITE << UAVOBJ_ACCESS_SHIFT |
            ACCESS_READWRITE << UAVOBJ_GCS_ACCESS_SHIFT |
            0 << UAVOBJ_TELEMETRY_ACKED_SHIFT |
            0 << UAVOBJ_GCS_TELEMETRY_ACKED_SHIFT |
            UPDATEMODE_PERIODIC << UAVOBJ_TELEMETRY_UPDATE_MODE_SHIFT |
            UPDATEMODE_MANUAL << UAVOBJ_GCS_TELEMETRY_UPDATE_MODE_SHIFT |
            UPDATEMODE_MANUAL << UAVOBJ_LOGGING_UPDATE_MODE_SHIFT;
        metadata.telemetryUpdatePeriod = 1000;
        metadata.gcsTelemetryUpdatePeriod = 0;
        metadata.loggingUpdatePeriod = 0;
        UAVObjSetMetadata(obj, &metadata);
    }
}

/**
 * Get object handle
 */
UAVObjHandle StabilizationDesiredHandle()
{
    return handle;
}

/**
 * Get/Set object Functions
 */
void StabilizationDesiredRollSet(float *NewRoll)
{
    UAVObjSetDataField(StabilizationDesiredHandle(), (void *)NewRoll, offsetof(StabilizationDesiredData, Roll), sizeof(float));
}
void StabilizationDesiredRollGet(float *NewRoll)
{
    UAVObjGetDataField(StabilizationDesiredHandle(), (void *)NewRoll, offsetof(StabilizationDesiredData, Roll), sizeof(float));
}
void StabilizationDesiredPitchSet(float *NewPitch)
{
    UAVObjSetDataField(StabilizationDesiredHandle(), (void *)NewPitch, offsetof(StabilizationDesiredData, Pitch), sizeof(float));
}
void StabilizationDesiredPitchGet(float *NewPitch)
{
    UAVObjGetDataField(StabilizationDesiredHandle(), (void *)NewPitch, offsetof(StabilizationDesiredData, Pitch), sizeof(float));
}
void StabilizationDesiredYawSet(float *NewYaw)
{
    UAVObjSetDataField(StabilizationDesiredHandle(), (void *)NewYaw, offsetof(StabilizationDesiredData, Yaw), sizeof(float));
}
void StabilizationDesiredYawGet(float *NewYaw)
{
    UAVObjGetDataField(StabilizationDesiredHandle(), (void *)NewYaw, offsetof(StabilizationDesiredData, Yaw), sizeof(float));
}
void StabilizationDesiredThrustSet(float *NewThrust)
{
    UAVObjSetDataField(StabilizationDesiredHandle(), (void *)NewThrust, offsetof(StabilizationDesiredData, Thrust), sizeof(float));
}
void StabilizationDesiredThrustGet(float *NewThrust)
{
    UAVObjGetDataField(StabilizationDesiredHandle(), (void *)NewThrust, offsetof(StabilizationDesiredData, Thrust), sizeof(float));
}
void StabilizationDesiredStabilizationModeSet( StabilizationDesiredStabilizationModeData *NewStabilizationMode )
{
    UAVObjSetDataField(StabilizationDesiredHandle(), (void *)NewStabilizationMode, offsetof(StabilizationDesiredData, StabilizationMode), 4*sizeof(StabilizationDesiredStabilizationModeOptions));
}
void StabilizationDesiredStabilizationModeGet( StabilizationDesiredStabilizationModeData *NewStabilizationMode )
{
    UAVObjGetDataField(StabilizationDesiredHandle(), (void *)NewStabilizationMode, offsetof(StabilizationDesiredData, StabilizationMode), 4*sizeof(StabilizationDesiredStabilizationModeOptions));
}
void StabilizationDesiredStabilizationModeArraySet( StabilizationDesiredStabilizationModeOptions *NewStabilizationMode )
{
    UAVObjSetDataField(StabilizationDesiredHandle(), (void *)NewStabilizationMode, offsetof(StabilizationDesiredData, StabilizationMode), 4*sizeof(StabilizationDesiredStabilizationModeOptions));
}
void StabilizationDesiredStabilizationModeArrayGet( StabilizationDesiredStabilizationModeOptions *NewStabilizationMode )
{
    UAVObjGetDataField(StabilizationDesiredHandle(), (void *)NewStabilizationMode, offsetof(StabilizationDesiredData, StabilizationMode), 4*sizeof(StabilizationDesiredStabilizationModeOptions));
}


/**
 * @}
 */
