
//!
//! Data model used to expose communications service telemetry
//! information over the GraphQL interface.
//!

use comms_service::CommsTelemetry;
use crate::comms::LocalComms;

use std::sync::{Arc, Mutex};
use log::*;

#[derive(Clone)]
pub struct Subsystem {
    telem: Arc<Mutex<CommsTelemetry>>,
    pub local: Arc<Mutex<LocalComms>>,
}

impl Subsystem {
    pub fn new(telem: Arc<Mutex<CommsTelemetry>>, local: Arc<Mutex<LocalComms>>) -> Subsystem {
        Subsystem { telem, local }
    }

    pub fn failed_packets_up(&self) -> Result<i32, String> {
        match self.telem.lock() {
            Ok(data) => Ok(data.failed_packets_up),
            Err(_) => Err("Failed to lock telemetry".to_owned()),
        }
    }

    pub fn failed_packets_down(&self) -> Result<i32, String> {
        match self.telem.lock() {
            Ok(data) => Ok(data.failed_packets_down),
            Err(_) => Err("Failed to lock telemetry".to_owned()),
        }
    }

    pub fn packets_up(&self) -> Result<i32, String> {
        match self.telem.lock() {
            Ok(data) => Ok(data.packets_up),
            Err(_) => Err("Failed to lock telemetry".to_owned()),
        }
    }

    pub fn packets_down(&self) -> Result<i32, String> {
        match self.telem.lock() {
            Ok(data) => Ok(data.packets_down),
            Err(_) => Err("Failed to lock telemetry".to_owned()),
        }
    }

    pub fn errors(&self) -> Result<Vec<String>, String> {
        match self.telem.lock() {
            Ok(data) => {
                Ok(data.errors.to_owned())
            }
            Err(_) => Err("Failed to lock telemetry".to_owned()),
        }
    }

    pub fn get_alive(&self) -> Result<bool, String> {
        match self.local.lock() {
            Ok(local) => Ok(local.socket.get_alive().map_err(|e| e.to_string())?),
            Err(_) => Err("Failed to lock local".to_owned()),
        }
    }

}
