//
// Copyright (C) 2018 Kubos Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License")
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Contributed by: William Greer (wgreer184@gmail.com) and Sam Justice (sam.justice1@gmail.com)
//

use comms_service::CommsResult;
use failure::bail;
use std::net::UdpSocket;
use std::sync::{Arc, Mutex};
use log::*;

pub struct LocalComms {
    pub socket: UdpSocket,
    pub gateway_ip: String,
    pub gateway_port: u16,
}

impl LocalComms {
    pub fn new(
        listening_ip: &str,
        listening_port: u16,
        gateway_ip: &str,
        gateway_port: u16,
    ) -> CommsResult<Self> {
        let socket = UdpSocket::bind((listening_ip, listening_port))?;
        Ok(LocalComms {
            socket,
            gateway_ip: gateway_ip.to_owned(),
            gateway_port,
        })
    }
    pub fn read(&self) -> CommsResult<Vec<u8>> {
        let mut buf = [0; 4096];
        let (size, _) = self.socket.recv_from(&mut buf)?;
        Ok(buf[0..size].to_vec())
    }

    pub fn write(&self, data: &[u8]) -> CommsResult<()> {
        let result = self.socket
            .send_to(data, (self.gateway_ip.as_str(), self.gateway_port))?;
        debug!("sent {} bytes", result);
        Ok(())
    }

    // pub fn get_alive(&self) -> CommsResult<bool> {
    //     if let Ok(addr) = self.socket.local_addr().unwrap() {
    //         return Ok(true)
    //     } else {
    //         return Ok(false)
    //     }
    // }
}

// Function to allow reading from a UDP socket.
pub fn net_read(socket: &Arc<Mutex<LocalComms>>) -> CommsResult<Vec<u8>> {
    debug!("READING");
    if let Ok(socket) = socket.lock() {
        debug!("locked and loaded");
        let res = socket.read(); // program will wait here until it received a message
        vec_to_str(&res);
        res
    } else {
        debug!("Failed to lock socket");
        bail!("Failed to lock socket")
    }
}

fn vec_to_str(buf: &CommsResult<Vec<u8>>) {
    if let Ok(res2) = buf {
            
        let s = match str::from_utf8(res2.as_slice()) {
            Ok(v) => v,
            Err(e) => panic!("Invalid UTF-8 sequence: {}", e),
        };

        debug!("result: {}", s);
    }
}

// Function to allow writing over a UDP socket.
pub fn net_write(socket: &Arc<Mutex<LocalComms>>, data: &[u8]) -> CommsResult<()> {
    if let Ok(socket) = socket.lock() {
        debug!("writing data: {}", String::from_utf8_lossy(data));
        socket.write(data)
    } else {
        bail!("Failed to lock socket")
    }
}
