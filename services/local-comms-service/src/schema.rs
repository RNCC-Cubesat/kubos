//!
//! GraphQL schema for exposing communications service
//! telemetry information.
//!

use juniper::FieldResult;
use crate::model::Subsystem;

type Context = kubos_service::Context<Subsystem>;

pub struct QueryRoot;

graphql_object!(QueryRoot: Context as "Query" |&self| {
    // Test query to verify service is running without attempting
    // to communicate with the underlying subsystem
    field ping() -> FieldResult<String>
    {
        Ok(String::from("pong"))
    }

    // Request number of bad uplink packets
    field failed_packets_up(&executor) -> FieldResult<i32>
    {
        Ok(executor.context().subsystem().failed_packets_up()?)
    }

    // Request number of bad downlink packets
    field failed_packets_down(&executor) -> FieldResult<i32>
    {
        Ok(executor.context().subsystem().failed_packets_down()?)
    }

    // Request number of packets successfully uplinked
    field packets_up(&executor) -> FieldResult<i32>
    {
        Ok(executor.context().subsystem().packets_up()?)
    }

    // Request number of packets successfully downlinked
    field packets_down(&executor) -> FieldResult<i32>
    {
        Ok(executor.context().subsystem().packets_down()?)
    }

    // Request errors that have occured
    field errors(&executor) -> FieldResult<Vec<String>>
    {
        Ok(executor.context().subsystem().errors()?)
    }
});

pub struct MutationRoot;

// Base GraphQL mutation model
graphql_object!(MutationRoot: Context as "Mutation" |&self| {

});