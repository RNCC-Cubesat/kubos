/*
* Copyright (C) 2017 Kubos Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#pragma once

#include "command-and-control/types.h"
#include "tinycbor/cbor.h"


bool encode_packet(CborDataWrapper *data_wrapper, CNCCommandPacket * packet);

bool encode_command(CborDataWrapper * data_wrapper, CNCCommandPacket * packet, CborEncoder * encoder, CborEncoder * container);

bool start_encode_response(int message_type, CborDataWrapper * data_wrapper, CNCCommandPacket * packet);

bool finish_encode_response_and_send(CborDataWrapper * data_wrapper, CborEncoder *encoder, CborEncoder * container);

bool parse_processing_error(CborParser * parser, CborValue * map);

bool parse_command_result( CborParser * parser, CborValue * map);

bool parse (CNCCommandPacket * command_packet, int argc, char ** argv);
