
//!
//! Data model used to expose communications service telemetry
//! information over the GraphQL interface.
//!

use comms_service::CommsTelemetry;
use std::sync::{Arc, Mutex};

#[derive(Clone)]
pub struct Subsystem {
    telem: Arc<Mutex<CommsTelemetry>>,
}

impl Subsystem {
    pub fn new(telem: Arc<Mutex<CommsTelemetry>>) -> Subsystem {
        Subsystem { telem }
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
}
