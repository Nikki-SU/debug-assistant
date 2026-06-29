// debug-assistant GUI 主入口
// 对应 SPEC：项目一 §四.3 GUI

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        // TODO: 启动 server sidecar（如果 server 已打包为可执行文件）
        // TODO: 注册 Tauri 命令（例如 open_data_dir, copy_report_to_clipboard）
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
