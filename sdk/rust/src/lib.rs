//! debug-assistant Rust SDK
//! 对应 SPEC：项目一 §六.3

use std::collections::HashMap;

pub struct Debugger {
    project: String,
    module: String,
    base_url: String,
    enabled: bool,
}

impl Debugger {
    pub fn new(project: &str, module: &str, host: &str, port: u16) -> Self {
        Self {
            project: project.to_string(),
            module: module.to_string(),
            base_url: format!("http://{}:{}", host, port),
            enabled: true,
        }
    }

    /// 上报错误，返回 error_id。失败时不应让业务侧崩溃。
    pub fn report<E: std::fmt::Display>(
        &self,
        _error: &E,
        _context: &HashMap<String, String>,
        _logs: &[String],
    ) -> Option<String> {
        if !self.enabled {
            return None;
        }
        // TODO: reqwest POST /api/report
        unimplemented!()
    }

    /// 回传解决方案。
    pub fn resolve(&self, _error_id: &str, _solution: &str, _related_changes: Option<&str>) -> bool {
        // TODO: reqwest POST /api/resolve
        unimplemented!()
    }
}
