//! debug-assistant Rust SDK.
//!
//! 设计原则：失败静默降级（Result::Err 只记 log，不向调用方扩散 panic）。
//!
//! ```no_run
//! use debug_assistant_sdk::{Debugger, ReportPayload};
//! let dbg = Debugger::new("PaperAssistant", "backend");
//! let _ = dbg.report(&ReportPayload {
//!     error_type: "TimeoutError",
//!     error_message: "请求超时",
//!     ..Default::default()
//! });
//! ```

use std::time::Duration;

use serde::{Deserialize, Serialize};

const SDK_NAME: &str = "debug-assistant-rs/0.1.0";

#[derive(Debug, Clone)]
pub struct Debugger {
    pub project: String,
    pub module: String,
    pub host: String,
    pub port: u16,
    pub enabled: bool,
    pub timeout: Duration,
}

impl Debugger {
    pub fn new(project: impl Into<String>, module: impl Into<String>) -> Self {
        Self {
            project: project.into(),
            module: module.into(),
            host: std::env::var("DEBUG_ASSISTANT_HOST").unwrap_or_else(|_| "127.0.0.1".to_string()),
            port: std::env::var("DEBUG_ASSISTANT_PORT")
                .ok()
                .and_then(|s| s.parse().ok())
                .unwrap_or(8765),
            enabled: std::env::var("DEBUG_ASSISTANT_ENABLED")
                .map(|v| !matches!(v.to_lowercase().as_str(), "false" | "0" | "no" | "off"))
                .unwrap_or(true),
            timeout: Duration::from_secs(2),
        }
    }

    pub fn with_endpoint(mut self, host: impl Into<String>, port: u16) -> Self {
        self.host = host.into();
        self.port = port;
        self
    }

    pub fn with_timeout(mut self, t: Duration) -> Self {
        self.timeout = t;
        self
    }

    fn base_url(&self) -> String {
        format!("http://{}:{}", self.host, self.port)
    }

    pub fn report(&self, payload: &ReportPayload) -> Option<String> {
        if !self.enabled {
            return None;
        }
        let body = ReportBody::from_payload(self, payload);
        let url = format!("{}/api/report", self.base_url());
        match post_json::<ReportBody, ReportCreated>(&url, &body, self.timeout) {
            Ok(r) => Some(r.error_id),
            Err(e) => {
                eprintln!("[debug-assistant] report 失败（已降级）: {e}");
                None
            }
        }
    }

    pub fn resolve(&self, error_id: &str, solution: &str, related_changes: Option<&str>) -> bool {
        if !self.enabled {
            return false;
        }
        let body = ResolveBody {
            error_id: error_id.to_string(),
            solution: solution.to_string(),
            related_changes: related_changes.map(|s| s.to_string()),
        };
        let url = format!("{}/api/resolve", self.base_url());
        match post_json::<ResolveBody, ResolveResult>(&url, &body, self.timeout) {
            Ok(r) => r.status == "resolved",
            Err(e) => {
                eprintln!("[debug-assistant] resolve 失败（已降级）: {e}");
                false
            }
        }
    }
}

#[derive(Default, Debug, Clone)]
pub struct ReportPayload<'a> {
    pub error_type: &'a str,
    pub error_message: &'a str,
    pub stack_trace: Option<&'a str>,
    pub severity: Option<&'a str>,
    pub user_action: Option<&'a str>,
    pub stage: Option<&'a str>,
    pub session_id: Option<&'a str>,
    pub context: Vec<(String, String)>,
    pub logs: Vec<String>,
    pub env: Vec<(String, String)>,
}

#[derive(Serialize)]
struct ReportBody {
    project: String,
    module: String,
    error_type: String,
    error_message: String,
    severity: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    stack_trace: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    user_action: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stage: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    session_id: Option<String>,
    extra_context_table: std::collections::BTreeMap<String, String>,
    logs: Vec<String>,
    env: std::collections::BTreeMap<String, String>,
}

impl ReportBody {
    fn from_payload(dbg: &Debugger, p: &ReportPayload<'_>) -> Self {
        let mut env: std::collections::BTreeMap<String, String> = p
            .env
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();
        env.entry("SDK".to_string()).or_insert_with(|| SDK_NAME.to_string());
        Self {
            project: dbg.project.clone(),
            module: dbg.module.clone(),
            error_type: p.error_type.to_string(),
            error_message: p.error_message.to_string(),
            severity: p.severity.unwrap_or("error").to_string(),
            stack_trace: p.stack_trace.map(|s| s.to_string()),
            user_action: p.user_action.map(|s| s.to_string()),
            stage: p.stage.map(|s| s.to_string()),
            session_id: p.session_id.map(|s| s.to_string()),
            extra_context_table: p.context.iter().cloned().collect(),
            logs: p.logs.clone(),
            env,
        }
    }
}

#[derive(Deserialize)]
struct ReportCreated {
    error_id: String,
    #[allow(dead_code)]
    path: String,
    #[allow(dead_code)]
    url: String,
}

#[derive(Serialize)]
struct ResolveBody {
    error_id: String,
    solution: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    related_changes: Option<String>,
}

#[derive(Deserialize)]
struct ResolveResult {
    #[allow(dead_code)]
    error_id: String,
    status: String,
    #[allow(dead_code)]
    resolved_at: String,
}

fn post_json<TReq: Serialize, TResp: serde::de::DeserializeOwned>(
    url: &str,
    body: &TReq,
    timeout: Duration,
) -> Result<TResp, String> {
    let resp = ureq::post(url)
        .timeout(timeout)
        .set("Content-Type", "application/json; charset=utf-8")
        .send_json(serde_json::to_value(body).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    resp.into_json::<TResp>().map_err(|e| e.to_string())
}
