use getopts::Options;
use kubos_app::logging_setup;
use std::{env, process, time::Duration};

const DEFAULT_TIMEOUT: Option<Duration> = Some(Duration::from_secs(10));
const DEFAULT_PATH: &str = "/etc/kubos-config.toml";

fn print_usage(program: &str, opts: Options) {
    let brief = format!("usage: {} [-h] [--config CONFIG]", program);
    print!("{}", opts.usage(&brief));
}

fn main() {
    logging_setup!("my-mission-app");
    let mut args = env::args();
    let program = args
        .next()
        .unwrap_or_else(|| String::from("my-mission-app"));
    let mut parser = Options::new();

    parser.optopt(
        "c",
        "config",
        "System config filw which should be used",
        "CONFIG",
    );
    parser.optflag("h", "help", "show this help message and exit");

    let matches = match parser.parse(args) {
        Ok(m) => m,
        Err(f) => panic!(f.to_string()),
    };

    if matches.opt_present("h") {
        print_usage(&program, parser);
        process::exit(0);
    }

    let path = matches
        .opt_str("c")
        .unwrap_or_else(|| DEFAULT_PATH.to_string());

    let services =
        kubos_app::ServiceConfig::new_from_path("monitor-service", path.clone()).unwrap();

    let request = "{ ping }";

    let response = kubos_app::query(&services, request, DEFAULT_TIMEOUT);
    let status = match response {
        Ok(resp) => {
            let data = &resp["ping"];

            if data.as_str().map_or(false, |d| d == "pong") {
                println!("We got a pong!");
                "Okay"
            } else {
                println!("Unexpected monitor service response {}", data);
                "Unexpected"
            }
        }
        Err(e) => {
            eprintln!("Something went wrong: {}", e);
            "Error"
        }
    };

    let request = format!(
        r#"mutation {{
        insert(subsystem: "OBC", parameter: "status", value: "{}") {{
            success,
            errors
        }}
    }}"#,
        status
    );

    let services = kubos_app::ServiceConfig::new_from_path("telemetry-service", path).unwrap();

    let response = kubos_app::query(&services, &request, DEFAULT_TIMEOUT);
    let resp = response.expect("Something went wrong");

    let data = &resp["insert"];
    let success = data["success"].as_bool().unwrap_or(false);
    let errors = &data["errors"];

    if !success {
        eprintln!("Telemetry insert contained errors: {}", errors);
        process::exit(1);
    } else {
        println!("Telemetry insert completed successfully:\n{}", data);
    }
}
