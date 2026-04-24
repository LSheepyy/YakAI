#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let app_data = app
                .handle()
                .path_resolver()
                .app_data_dir()
                .expect("failed to resolve app data dir");

            std::env::set_var("YAKAI_APP_DATA", &app_data);

            // In production the Python sidecar is bundled as an external binary.
            // In dev mode run `uvicorn main:app` from services/ai-core manually.
            #[cfg(not(debug_assertions))]
            {
                let sidecar = app_data.join("sidecar").join("ai-core");
                let _ = Command::new(&sidecar)
                    .env("YAKAI_APP_DATA", &app_data)
                    .spawn();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running YakAI");
}
