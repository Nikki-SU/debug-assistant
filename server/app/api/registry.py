"""项目注册表 + 全局设置的 REST API。

端点：
    GET    /api/registry            列出全部项目注册
    POST   /api/registry            upsert 项目注册（按 name 主键）
    DELETE /api/registry/{name}     删除项目注册
    GET    /api/settings            读取全局默认（default_open_with / default_custom_cmd）
    PUT    /api/settings            修改全局默认

设计要点：
- 注册表与 index.csv 解耦：未注册的 project 名仍可写报告。
- /api/projects 仍返回"按 index 聚合的项目树"——前端可把 registry 名集合并入展示。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings, update_global_settings
from ..models.error_report import (
    ProjectRegistry,
    RegistryUpsert,
    SettingsPatch,
    SettingsView,
)
from ..storage import delete_registry, load_registry, upsert_registry

router = APIRouter(tags=["registry"])


@router.get("/api/registry")
def list_registry(settings: Settings = Depends(get_settings)) -> dict:
    rows = load_registry(settings.registry_csv)
    return {"total": len(rows), "items": [r.model_dump() for r in rows]}


@router.post("/api/registry", response_model=ProjectRegistry)
def post_registry(
    payload: RegistryUpsert,
    settings: Settings = Depends(get_settings),
) -> ProjectRegistry:
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name 不能为空")
    item = ProjectRegistry(
        name=name,
        local_path=(payload.local_path or "").strip(),
        open_with=(payload.open_with or "").strip(),
        custom_cmd=payload.custom_cmd or "",
    )
    return upsert_registry(settings.registry_csv, item)


@router.delete("/api/registry/{name}")
def del_registry(name: str, settings: Settings = Depends(get_settings)) -> dict:
    ok = delete_registry(settings.registry_csv, name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"项目注册不存在: {name}")
    return {"ok": True, "name": name}


@router.get("/api/settings", response_model=SettingsView)
def get_settings_view(settings: Settings = Depends(get_settings)) -> SettingsView:
    return SettingsView(
        default_open_with=settings.default_open_with,
        default_custom_cmd=settings.default_custom_cmd,
    )


@router.put("/api/settings", response_model=SettingsView)
def put_settings(
    patch: SettingsPatch,
    settings: Settings = Depends(get_settings),
) -> SettingsView:
    updates: dict[str, str] = {}
    if patch.default_open_with is not None:
        v = patch.default_open_with.strip()
        if v not in ("none", "copy_path", "explorer", "vscode", "custom"):
            raise HTTPException(
                status_code=400,
                detail="default_open_with 必须是 none / copy_path / explorer / vscode / custom 之一",
            )
        updates["default_open_with"] = v
    if patch.default_custom_cmd is not None:
        updates["default_custom_cmd"] = patch.default_custom_cmd
    new_settings = update_global_settings(updates)
    return SettingsView(
        default_open_with=new_settings.default_open_with,
        default_custom_cmd=new_settings.default_custom_cmd,
    )
