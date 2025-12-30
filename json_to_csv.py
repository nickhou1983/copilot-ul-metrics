#!/usr/bin/env python3
"""GitHub Copilot User Level Metrics - JSON to CSV Converter.

Enhancements in this version:
1. Aggregate duplicate user-day records by summing metric fields.
2. Provide dedicated code-completion summaries including acceptance ratios.
3. Report Chat-generated lines of code derived from IDE totals minus
   code-completion suggestions.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


class CopilotMetricsConverter:
    """Convert GitHub Copilot user-level metrics from JSON to CSV."""

    BASE_SUM_FIELDS = [
        "user_initiated_interaction_count",
        "code_generation_activity_count",
        "code_acceptance_activity_count",
        "loc_suggested_to_add_sum",
        "loc_suggested_to_delete_sum",
        "loc_added_sum",
        "loc_deleted_sum",
    ]

    def __init__(self, json_file: str):
        self.json_file = Path(json_file)
        self.raw_data = self._load_raw_json()
        self.data = self._aggregate_records(self.raw_data)
        print(
            f"✅ 数据聚合完成: {len(self.raw_data)} 条原始记录 → "
            f"{len(self.data)} 条用户日汇总记录"
        )

    # ------------------------------------------------------------------
    # Load and aggregate JSON
    # ------------------------------------------------------------------
    def _load_raw_json(self) -> List[Dict[str, Any]]:
        """Read JSON content (supports JSON-lines and JSON-array formats)."""
        print(f"📖 正在读取 JSON 文件: {self.json_file}")
        content = self.json_file.read_text(encoding="utf-8").strip()
        if not content:
            return []

        records: List[Dict[str, Any]] = []
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records = json.loads(content)
                break

        print(f"✅ 成功读取 {len(records)} 条原始记录")
        return records

    def _aggregate_records(self, records: Iterable[Dict[str, Any]]):
        """Aggregate records by user name, summing their fields across all days."""
        aggregates: Dict[Tuple[Any, ...], Dict[str, Any]] = {}

        for record in records:
            # 按用户名称汇总（不再按日期分组）
            key = (
                record.get("user_login"),
                record.get("enterprise_id"),
                record.get("user_id"),
            )
            if key not in aggregates:
                aggregates[key] = self._initialise_aggregate(record)

            aggregate = aggregates[key]
            self._aggregate_base_fields(aggregate, record)
            self._aggregate_totals_by_ide(aggregate["totals_by_ide"], record.get("totals_by_ide", []))
            self._aggregate_totals_by_feature(aggregate["totals_by_feature"], record.get("totals_by_feature", []))
            self._aggregate_language_feature(
                aggregate["totals_by_language_feature"], record.get("totals_by_language_feature", [])
            )
            self._aggregate_language_model(
                aggregate["totals_by_language_model"], record.get("totals_by_language_model", [])
            )
            self._aggregate_model_feature(
                aggregate["totals_by_model_feature"], record.get("totals_by_model_feature", [])
            )
            
            # 更新日期范围
            aggregate["report_start_day"] = min(
                aggregate["report_start_day"] or record.get("report_start_day", ""),
                record.get("report_start_day", "")
            ) if aggregate["report_start_day"] else record.get("report_start_day", "")
            
            aggregate["report_end_day"] = max(
                aggregate["report_end_day"] or record.get("report_end_day", ""),
                record.get("report_end_day", "")
            ) if aggregate["report_end_day"] else record.get("report_end_day", "")

        aggregated_list = [self._finalise_aggregate(entry) for entry in aggregates.values()]
        aggregated_list.sort(key=lambda item: item["user_login"])
        return aggregated_list

    def _initialise_aggregate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        aggregate = {
            "report_start_day": record.get("report_start_day"),
            "report_end_day": record.get("report_end_day"),
            "day": record.get("day"),
            "enterprise_id": record.get("enterprise_id"),
            "user_id": record.get("user_id"),
            "user_login": record.get("user_login"),
            "used_agent": bool(record.get("used_agent", False)),
            "used_chat": bool(record.get("used_chat", False)),
            "totals_by_ide": {},
            "totals_by_feature": {},
            "totals_by_language_feature": {},
            "totals_by_language_model": {},
            "totals_by_model_feature": {},
        }
        for field in self.BASE_SUM_FIELDS:
            aggregate[field] = 0
        return aggregate

    def _aggregate_base_fields(self, aggregate: Dict[str, Any], record: Dict[str, Any]) -> None:
        for field in self.BASE_SUM_FIELDS:
            aggregate[field] += record.get(field, 0)
        aggregate["used_agent"] = aggregate["used_agent"] or record.get("used_agent", False)
        aggregate["used_chat"] = aggregate["used_chat"] or record.get("used_chat", False)

    def _aggregate_totals_by_ide(self, container: Dict[str, Dict[str, Any]], items: Iterable[Dict[str, Any]]) -> None:
        sum_fields = [
            "user_initiated_interaction_count",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]
        for item in items:
            ide = item.get("ide", "unknown")
            entry = container.get(ide)
            if entry is None:
                entry = {"ide": ide}
                for field in sum_fields:
                    entry[field] = 0
                entry["last_known_plugin_version"] = None
                entry["last_known_ide_version"] = None
                container[ide] = entry
            for field in sum_fields:
                entry[field] += item.get(field, 0)
            entry["last_known_plugin_version"] = self._choose_latest(
                entry.get("last_known_plugin_version"), item.get("last_known_plugin_version")
            )
            entry["last_known_ide_version"] = self._choose_latest(
                entry.get("last_known_ide_version"), item.get("last_known_ide_version")
            )

    def _aggregate_totals_by_feature(self, container: Dict[str, Dict[str, Any]], items: Iterable[Dict[str, Any]]) -> None:
        sum_fields = [
            "user_initiated_interaction_count",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]
        for item in items:
            feature = item.get("feature", "unknown")
            entry = container.get(feature)
            if entry is None:
                entry = {"feature": feature}
                for field in sum_fields:
                    entry[field] = 0
                container[feature] = entry
            for field in sum_fields:
                entry[field] += item.get(field, 0)

    def _aggregate_language_feature(
        self,
        container: Dict[Tuple[str, str], Dict[str, Any]],
        items: Iterable[Dict[str, Any]],
    ) -> None:
        sum_fields = [
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]
        for item in items:
            key = (item.get("language", "unknown"), item.get("feature", "unknown"))
            entry = container.get(key)
            if entry is None:
                entry = {"language": key[0], "feature": key[1]}
                for field in sum_fields:
                    entry[field] = 0
                container[key] = entry
            for field in sum_fields:
                entry[field] += item.get(field, 0)

    def _aggregate_language_model(
        self,
        container: Dict[Tuple[str, str], Dict[str, Any]],
        items: Iterable[Dict[str, Any]],
    ) -> None:
        sum_fields = [
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]
        for item in items:
            key = (item.get("language", "unknown"), item.get("model", "unknown"))
            entry = container.get(key)
            if entry is None:
                entry = {"language": key[0], "model": key[1]}
                for field in sum_fields:
                    entry[field] = 0
                container[key] = entry
            for field in sum_fields:
                entry[field] += item.get(field, 0)

    def _aggregate_model_feature(
        self,
        container: Dict[Tuple[str, str], Dict[str, Any]],
        items: Iterable[Dict[str, Any]],
    ) -> None:
        sum_fields = [
            "user_initiated_interaction_count",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]
        for item in items:
            key = (item.get("model", "unknown"), item.get("feature", "unknown"))
            entry = container.get(key)
            if entry is None:
                entry = {"model": key[0], "feature": key[1]}
                for field in sum_fields:
                    entry[field] = 0
                container[key] = entry
            for field in sum_fields:
                entry[field] += item.get(field, 0)

    def _finalise_aggregate(self, aggregate: Dict[str, Any]) -> Dict[str, Any]:
        aggregate["totals_by_ide"] = sorted(aggregate["totals_by_ide"].values(), key=lambda item: item["ide"])
        aggregate["totals_by_feature"] = sorted(
            aggregate["totals_by_feature"].values(), key=lambda item: item["feature"]
        )
        aggregate["totals_by_language_feature"] = sorted(
            aggregate["totals_by_language_feature"].values(),
            key=lambda item: (item["language"], item["feature"]),
        )
        aggregate["totals_by_language_model"] = sorted(
            aggregate["totals_by_language_model"].values(),
            key=lambda item: (item["language"], item["model"]),
        )
        aggregate["totals_by_model_feature"] = sorted(
            aggregate["totals_by_model_feature"].values(),
            key=lambda item: (item["model"], item["feature"]),
        )
        return aggregate

    @staticmethod
    def _choose_latest(existing: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        if not candidate:
            return existing
        if not existing:
            return candidate
        if candidate.get("sampled_at", "") >= existing.get("sampled_at", ""):
            return candidate
        return existing

    # ------------------------------------------------------------------
    # CSV exports
    # ------------------------------------------------------------------
    def export_user_summary(self, output_file: Path) -> Path:
        print("\n📊 导出用户总体指标（按用户汇总）...")
        headers = [
            "用户名",
            "报告开始日期",
            "报告结束日期",
            "Code Completion 代码生成次数",
            "Code Completion 代码接受次数",
            "Code Completion 建议代码行数",
            "Code Completion 接受代码行数",
            "Chat Ask 交互次数",
            "Chat Ask 接受次数",
            "Chat Ask 建议代码行数",
            "Chat Ask 接受代码行数",
            "Chat Agent 建议代码行数",
            "Chat Agent 接受代码行数",
            "Agent Edit 添加代码行数",
            "Agent Edit 删除代码行数",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            cc_metrics = self._extract_feature_metrics(record, "code_completion")
            cc_code_gen = cc_metrics.get("code_generation_activity_count", 0)
            cc_code_accept = cc_metrics.get("code_acceptance_activity_count", 0)
            cc_loc_suggested = cc_metrics.get("loc_suggested_to_add_sum", 0)
            cc_loc_added = cc_metrics.get("loc_added_sum", 0)

            # 提取 chat_panel_ask_mode 相关指标
            ask_metrics = self._extract_feature_metrics(record, "chat_panel_ask_mode")
            ask_interaction = ask_metrics.get("user_initiated_interaction_count", 0)
            ask_acceptance = ask_metrics.get("code_acceptance_activity_count", 0)
            ask_loc_suggested = ask_metrics.get("loc_suggested_to_add_sum", 0)
            ask_loc_added = ask_metrics.get("loc_added_sum", 0)

            # 提取 chat_panel_agent_mode 相关指标
            agent_mode_metrics = self._extract_feature_metrics(record, "chat_panel_agent_mode")
            agent_mode_loc_suggested = agent_mode_metrics.get("loc_suggested_to_add_sum", 0)
            agent_mode_loc_added = agent_mode_metrics.get("loc_added_sum", 0)

            # 提取 agent_edit 相关指标
            agent_edit_metrics = self._extract_feature_metrics(record, "agent_edit")
            agent_edit_loc_added = agent_edit_metrics.get("loc_added_sum", 0)
            agent_edit_loc_deleted = agent_edit_metrics.get("loc_deleted_sum", 0)

            rows.append(
                {
                    "用户名": record.get("user_login", ""),
                    "报告开始日期": record.get("report_start_day", ""),
                    "报告结束日期": record.get("report_end_day", ""),
                    "Code Completion 代码生成次数": cc_code_gen,
                    "Code Completion 代码接受次数": cc_code_accept,
                    "Code Completion 建议代码行数": cc_loc_suggested,
                    "Code Completion 接受代码行数": cc_loc_added,
                    "Chat Ask 交互次数": ask_interaction,
                    "Chat Ask 接受次数": ask_acceptance,
                    "Chat Ask 建议代码行数": ask_loc_suggested,
                    "Chat Ask 接受代码行数": ask_loc_added,
                    "Chat Agent 建议代码行数": agent_mode_loc_suggested,
                    "Chat Agent 接受代码行数": agent_mode_loc_added,
                    "Agent Edit 添加代码行数": agent_edit_loc_added,
                    "Agent Edit 删除代码行数": agent_edit_loc_deleted,
                }
            )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_by_ide(self, output_file: Path) -> Path:
        print("\n📊 导出 IDE 维度统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "ide",
            "user_initiated_interaction_count",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
            "plugin",
            "plugin_version",
            "plugin_sampled_at",
            "ide_version",
            "ide_version_sampled_at",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            for ide_data in record.get("totals_by_ide", []):
                plugin_info = ide_data.get("last_known_plugin_version") or {}
                ide_version_info = ide_data.get("last_known_ide_version") or {}
                rows.append(
                    {
                        "report_start_day": record.get("report_start_day", ""),
                        "report_end_day": record.get("report_end_day", ""),
                        "day": record.get("day", ""),
                        "enterprise_id": record.get("enterprise_id", ""),
                        "user_id": record.get("user_id", ""),
                        "user_login": record.get("user_login", ""),
                        "ide": ide_data.get("ide", ""),
                        "user_initiated_interaction_count": ide_data.get("user_initiated_interaction_count", 0),
                        "code_generation_activity_count": ide_data.get("code_generation_activity_count", 0),
                        "code_acceptance_activity_count": ide_data.get("code_acceptance_activity_count", 0),
                        "loc_suggested_to_add_sum": ide_data.get("loc_suggested_to_add_sum", 0),
                        "loc_suggested_to_delete_sum": ide_data.get("loc_suggested_to_delete_sum", 0),
                        "loc_added_sum": ide_data.get("loc_added_sum", 0),
                        "loc_deleted_sum": ide_data.get("loc_deleted_sum", 0),
                        "plugin": plugin_info.get("plugin", ""),
                        "plugin_version": plugin_info.get("plugin_version", ""),
                        "plugin_sampled_at": plugin_info.get("sampled_at", ""),
                        "ide_version": ide_version_info.get("ide_version", ""),
                        "ide_version_sampled_at": ide_version_info.get("sampled_at", ""),
                    }
                )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_by_feature(self, output_file: Path) -> Path:
        print("\n📊 导出功能维度统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "feature",
            "user_initiated_interaction_count",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            for feature_data in record.get("totals_by_feature", []):
                rows.append(
                    {
                        "report_start_day": record.get("report_start_day", ""),
                        "report_end_day": record.get("report_end_day", ""),
                        "day": record.get("day", ""),
                        "enterprise_id": record.get("enterprise_id", ""),
                        "user_id": record.get("user_id", ""),
                        "user_login": record.get("user_login", ""),
                        "feature": feature_data.get("feature", ""),
                        "user_initiated_interaction_count": feature_data.get("user_initiated_interaction_count", 0),
                        "code_generation_activity_count": feature_data.get("code_generation_activity_count", 0),
                        "code_acceptance_activity_count": feature_data.get("code_acceptance_activity_count", 0),
                        "loc_suggested_to_add_sum": feature_data.get("loc_suggested_to_add_sum", 0),
                        "loc_suggested_to_delete_sum": feature_data.get("loc_suggested_to_delete_sum", 0),
                        "loc_added_sum": feature_data.get("loc_added_sum", 0),
                        "loc_deleted_sum": feature_data.get("loc_deleted_sum", 0),
                    }
                )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_by_language_feature(self, output_file: Path) -> Path:
        print("\n📊 导出编程语言 + 功能维度统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "language",
            "feature",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            for lf_data in record.get("totals_by_language_feature", []):
                rows.append(
                    {
                        "report_start_day": record.get("report_start_day", ""),
                        "report_end_day": record.get("report_end_day", ""),
                        "day": record.get("day", ""),
                        "enterprise_id": record.get("enterprise_id", ""),
                        "user_id": record.get("user_id", ""),
                        "user_login": record.get("user_login", ""),
                        "language": lf_data.get("language", ""),
                        "feature": lf_data.get("feature", ""),
                        "code_generation_activity_count": lf_data.get("code_generation_activity_count", 0),
                        "code_acceptance_activity_count": lf_data.get("code_acceptance_activity_count", 0),
                        "loc_suggested_to_add_sum": lf_data.get("loc_suggested_to_add_sum", 0),
                        "loc_suggested_to_delete_sum": lf_data.get("loc_suggested_to_delete_sum", 0),
                        "loc_added_sum": lf_data.get("loc_added_sum", 0),
                        "loc_deleted_sum": lf_data.get("loc_deleted_sum", 0),
                    }
                )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_by_language_model(self, output_file: Path) -> Path:
        print("\n📊 导出编程语言 + 模型维度统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "language",
            "model",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            for lm_data in record.get("totals_by_language_model", []):
                rows.append(
                    {
                        "report_start_day": record.get("report_start_day", ""),
                        "report_end_day": record.get("report_end_day", ""),
                        "day": record.get("day", ""),
                        "enterprise_id": record.get("enterprise_id", ""),
                        "user_id": record.get("user_id", ""),
                        "user_login": record.get("user_login", ""),
                        "language": lm_data.get("language", ""),
                        "model": lm_data.get("model", ""),
                        "code_generation_activity_count": lm_data.get("code_generation_activity_count", 0),
                        "code_acceptance_activity_count": lm_data.get("code_acceptance_activity_count", 0),
                        "loc_suggested_to_add_sum": lm_data.get("loc_suggested_to_add_sum", 0),
                        "loc_suggested_to_delete_sum": lm_data.get("loc_suggested_to_delete_sum", 0),
                        "loc_added_sum": lm_data.get("loc_added_sum", 0),
                        "loc_deleted_sum": lm_data.get("loc_deleted_sum", 0),
                    }
                )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_by_model_feature(self, output_file: Path) -> Path:
        print("\n📊 导出模型 + 功能维度统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "model",
            "feature",
            "user_initiated_interaction_count",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "loc_suggested_to_add_sum",
            "loc_suggested_to_delete_sum",
            "loc_added_sum",
            "loc_deleted_sum",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            for mf_data in record.get("totals_by_model_feature", []):
                rows.append(
                    {
                        "report_start_day": record.get("report_start_day", ""),
                        "report_end_day": record.get("report_end_day", ""),
                        "day": record.get("day", ""),
                        "enterprise_id": record.get("enterprise_id", ""),
                        "user_id": record.get("user_id", ""),
                        "user_login": record.get("user_login", ""),
                        "model": mf_data.get("model", ""),
                        "feature": mf_data.get("feature", ""),
                        "user_initiated_interaction_count": mf_data.get("user_initiated_interaction_count", 0),
                        "code_generation_activity_count": mf_data.get("code_generation_activity_count", 0),
                        "code_acceptance_activity_count": mf_data.get("code_acceptance_activity_count", 0),
                        "loc_suggested_to_add_sum": mf_data.get("loc_suggested_to_add_sum", 0),
                        "loc_suggested_to_delete_sum": mf_data.get("loc_suggested_to_delete_sum", 0),
                        "loc_added_sum": mf_data.get("loc_added_sum", 0),
                        "loc_deleted_sum": mf_data.get("loc_deleted_sum", 0),
                    }
                )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_code_completion_summary(self, output_file: Path) -> Path:
        print("\n📊 导出 Code Completion 专项统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "code_completion_code_generation_count",
            "code_completion_code_acceptance_count",
            "code_completion_loc_suggested_to_add_sum",
            "code_completion_loc_added_sum",
            "code_completion_acceptance_rate",
            "code_completion_loc_acceptance_rate",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            cc_metrics = self._extract_feature_metrics(record, "code_completion")
            code_gen = cc_metrics.get("code_generation_activity_count", 0)
            code_accept = cc_metrics.get("code_acceptance_activity_count", 0)
            loc_suggested = cc_metrics.get("loc_suggested_to_add_sum", 0)
            loc_added = cc_metrics.get("loc_added_sum", 0)

            rows.append(
                {
                    "report_start_day": record.get("report_start_day", ""),
                    "report_end_day": record.get("report_end_day", ""),
                    "day": record.get("day", ""),
                    "enterprise_id": record.get("enterprise_id", ""),
                    "user_id": record.get("user_id", ""),
                    "user_login": record.get("user_login", ""),
                    "code_completion_code_generation_count": code_gen,
                    "code_completion_code_acceptance_count": code_accept,
                    "code_completion_loc_suggested_to_add_sum": loc_suggested,
                    "code_completion_loc_added_sum": loc_added,
                    "code_completion_acceptance_rate": self._calculate_rate(code_accept, code_gen),
                    "code_completion_loc_acceptance_rate": self._calculate_rate(loc_added, loc_suggested),
                }
            )

        self._write_csv(output_file, headers, rows)
        return output_file

    def export_chat_loc_summary(self, output_file: Path) -> Path:
        print("\n📊 导出 Chat 生成代码行数统计...")
        headers = [
            "report_start_day",
            "report_end_day",
            "day",
            "enterprise_id",
            "user_id",
            "user_login",
            "total_loc_added_sum",
            "code_completion_loc_added_sum",
            "chat_loc_added_sum",
        ]

        rows: List[Dict[str, Any]] = []
        for record in self.data:
            cc_metrics = self._extract_feature_metrics(record, "code_completion")
            cc_loc_added = cc_metrics.get("loc_added_sum", 0)
            total_loc = self._sum_loc_added_from_ide(record)
            chat_loc = max(total_loc - cc_loc_added, 0)

            rows.append(
                {
                    "report_start_day": record.get("report_start_day", ""),
                    "report_end_day": record.get("report_end_day", ""),
                    "day": record.get("day", ""),
                    "enterprise_id": record.get("enterprise_id", ""),
                    "user_id": record.get("user_id", ""),
                    "user_login": record.get("user_login", ""),
                    "total_loc_added_sum": total_loc,
                    "code_completion_loc_added_sum": cc_loc_added,
                    "chat_loc_added_sum": chat_loc,
                }
            )

        self._write_csv(output_file, headers, rows)
        return output_file

    # ------------------------------------------------------------------
    # HTML Report Generation
    # ------------------------------------------------------------------
    def generate_html_report(self, output_file: Path) -> Path:
        """生成 HTML 格式的可视化报告"""
        print(f"📄 正在生成 HTML 报告: {output_file.name}")
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Copilot Metrics 报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
            color: #24292e;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #0969da;
        }}
        .header h1 {{
            color: #24292e;
            font-size: 36px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #57606a;
            font-size: 16px;
        }}
        .info-box {{
            background: linear-gradient(135deg, #f6f8fa 0%, #e1e4e8 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        .info-label {{
            font-size: 12px;
            color: #57606a;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .info-value {{
            font-size: 18px;
            color: #24292e;
            font-weight: bold;
        }}
        h2 {{
            color: #0969da;
            margin: 40px 0 20px;
            padding-left: 15px;
            border-left: 5px solid #0969da;
            font-size: 24px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }}
        .metric-card.green {{ background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%); }}
        .metric-card.blue {{ background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%); }}
        .metric-card.orange {{ background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); }}
        .metric-card.red {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .metric-card.purple {{ background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); }}
        .metric-icon {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 42px;
            font-weight: bold;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.95;
            font-weight: 500;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 14px;
            text-align: left;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            border-bottom: 1px solid #e1e4e8;
        }}
        tr:hover td {{
            background: #f6f8fa;
        }}
        .rank {{
            background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%);
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }}
        .rank.gold {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); }}
        .rank.silver {{ background: linear-gradient(135deg, #C0C0C0 0%, #808080 100%); }}
        .rank.bronze {{ background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%); }}
        .progress-bar {{
            background: #e1e4e8;
            height: 24px;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #56ab2f, #a8e063);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
            transition: width 0.3s ease;
            position: relative;
        }}
        .progress-fill::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }}
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin: 0 5px;
        }}
        .badge.success {{ background: #2ea44f; color: white; }}
        .badge.warning {{ background: #fb8500; color: white; }}
        .badge.info {{ background: #0969da; color: white; }}
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: #f6f8fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e1e4e8;
        }}
        .stat-box .number {{
            font-size: 28px;
            font-weight: bold;
            color: #0969da;
            margin-bottom: 5px;
        }}
        .stat-box .label {{
            font-size: 12px;
            color: #57606a;
            font-weight: 600;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e1e4e8;
            color: #57606a;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 GitHub Copilot Metrics 使用报告</h1>
            <div class="subtitle">企业 AI 编程助手使用情况分析</div>
        </div>
        
        <div class="info-box">
            <div class="info-item">
                <div class="info-label">报告期间</div>
                <div class="info-value">{self._get_date_range()}</div>
            </div>
            <div class="info-item">
                <div class="info-label">用户总数</div>
                <div class="info-value">{len(self.data)} 人</div>
            </div>
            <div class="info-item">
                <div class="info-label">生成时间</div>
                <div class="info-value">{self._get_current_time()}</div>
            </div>
        </div>

{self._generate_overall_metrics_html()}
{self._generate_feature_adoption_html()}
{self._generate_top_users_html()}
{self._generate_ide_stats_html()}
{self._generate_language_stats_html()}
        
        <div class="footer">
            <p>🤖 由 GitHub Copilot Metrics Converter 自动生成</p>
            <p>数据来源: {self.json_file.name}</p>
        </div>
    </div>
</body>
</html>
"""
        
        output_file.write_text(html_content, encoding='utf-8')
        print(f"   ✅ HTML 报告已生成")
        return output_file

    def _get_date_range(self) -> str:
        """获取数据的日期范围"""
        if not self.data:
            return "N/A"
        start = min(d.get("report_start_day", "") for d in self.data if d.get("report_start_day"))
        end = max(d.get("report_end_day", "") for d in self.data if d.get("report_end_day"))
        return f"{start} ~ {end}"

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def _generate_overall_metrics_html(self) -> str:
        """生成整体指标的 HTML"""
        total_generations = sum(d.get("code_generation_activity_count", 0) for d in self.data)
        total_acceptances = sum(d.get("code_acceptance_activity_count", 0) for d in self.data)
        total_loc_added = sum(d.get("loc_added_sum", 0) for d in self.data)
        total_interactions = sum(d.get("user_initiated_interaction_count", 0) for d in self.data)
        total_loc_suggested = sum(d.get("loc_suggested_to_add_sum", 0) for d in self.data)
        overall_acceptance = (total_acceptances / total_generations * 100) if total_generations > 0 else 0
        
        return f"""
        <h2>📈 整体统计指标</h2>
        <div class="metrics-grid">
            <div class="metric-card blue">
                <div class="metric-icon">🎯</div>
                <div class="metric-label">代码生成总次数</div>
                <div class="metric-value">{total_generations:,}</div>
            </div>
            <div class="metric-card green">
                <div class="metric-icon">✅</div>
                <div class="metric-label">代码接受总次数</div>
                <div class="metric-value">{total_acceptances:,}</div>
            </div>
            <div class="metric-card orange">
                <div class="metric-icon">📊</div>
                <div class="metric-label">整体接受率</div>
                <div class="metric-value">{overall_acceptance:.1f}%</div>
            </div>
            <div class="metric-card red">
                <div class="metric-icon">📝</div>
                <div class="metric-label">新增代码总行数</div>
                <div class="metric-value">{total_loc_added:,}</div>
            </div>
            <div class="metric-card purple">
                <div class="metric-icon">💬</div>
                <div class="metric-label">用户交互总次数</div>
                <div class="metric-value">{total_interactions:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">💡</div>
                <div class="metric-label">建议代码总行数</div>
                <div class="metric-value">{total_loc_suggested:,}</div>
            </div>
        </div>
        """

    def _generate_feature_adoption_html(self) -> str:
        """生成功能采用情况的 HTML"""
        used_agent = sum(1 for d in self.data if d.get("used_agent"))
        used_chat = sum(1 for d in self.data if d.get("used_chat"))
        used_both = sum(1 for d in self.data if d.get("used_agent") and d.get("used_chat"))
        total_users = len(self.data)
        
        agent_percent = (used_agent / total_users * 100) if total_users > 0 else 0
        chat_percent = (used_chat / total_users * 100) if total_users > 0 else 0
        both_percent = (used_both / total_users * 100) if total_users > 0 else 0
        
        return f"""
        <h2>🎯 功能采用情况</h2>
        <div class="stats-row">
            <div class="stat-box">
                <div class="number">{used_agent}</div>
                <div class="label">使用 Agent 的用户</div>
                <div style="margin-top: 10px;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {agent_percent}%">{agent_percent:.1f}%</div>
                    </div>
                </div>
            </div>
            <div class="stat-box">
                <div class="number">{used_chat}</div>
                <div class="label">使用 Chat 的用户</div>
                <div style="margin-top: 10px;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {chat_percent}%">{chat_percent:.1f}%</div>
                    </div>
                </div>
            </div>
            <div class="stat-box">
                <div class="number">{used_both}</div>
                <div class="label">同时使用两者</div>
                <div style="margin-top: 10px;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {both_percent}%">{both_percent:.1f}%</div>
                    </div>
                </div>
            </div>
            <div class="stat-box">
                <div class="number">{total_users - used_agent - used_chat + used_both}</div>
                <div class="label">仅使用 Code Completion</div>
            </div>
        </div>
        """

    def _generate_top_users_html(self) -> str:
        """生成 TOP 用户排行的 HTML"""
        top_users = sorted(self.data, key=lambda x: x.get("code_generation_activity_count", 0), reverse=True)[:15]
        
        rows = ""
        for i, user in enumerate(top_users, 1):
            username = user.get("user_login", "Unknown")
            generations = user.get("code_generation_activity_count", 0)
            acceptances = user.get("code_acceptance_activity_count", 0)
            loc = user.get("loc_added_sum", 0)
            interactions = user.get("user_initiated_interaction_count", 0)
            rate = (acceptances / generations * 100) if generations > 0 else 0
            
            rank_class = ""
            if i == 1:
                rank_class = "gold"
            elif i == 2:
                rank_class = "silver"
            elif i == 3:
                rank_class = "bronze"
            
            badges = ""
            if user.get("used_agent"):
                badges += '<span class="badge info">Agent</span>'
            if user.get("used_chat"):
                badges += '<span class="badge success">Chat</span>'
            
            rows += f"""
            <tr>
                <td><span class="rank {rank_class}">{i}</span></td>
                <td><strong>{username}</strong> {badges}</td>
                <td>{generations:,}</td>
                <td>{acceptances:,}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(rate, 100)}%">{rate:.1f}%</div>
                    </div>
                </td>
                <td>{loc:,}</td>
                <td>{interactions:,}</td>
            </tr>
            """
        
        return f"""
        <h2>🏆 TOP 15 最活跃用户</h2>
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>用户名</th>
                    <th>代码生成次数</th>
                    <th>代码接受次数</th>
                    <th>接受率</th>
                    <th>新增代码行数</th>
                    <th>交互次数</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_ide_stats_html(self) -> str:
        """生成 IDE 统计的 HTML"""
        ide_stats = {}
        
        for record in self.data:
            for ide_data in record.get("totals_by_ide", []):
                ide = ide_data.get("ide", "unknown")
                if ide not in ide_stats:
                    ide_stats[ide] = {
                        "users": set(),
                        "generations": 0,
                        "acceptances": 0,
                        "loc_added": 0
                    }
                ide_stats[ide]["users"].add(record.get("user_login"))
                ide_stats[ide]["generations"] += ide_data.get("code_generation_activity_count", 0)
                ide_stats[ide]["acceptances"] += ide_data.get("code_acceptance_activity_count", 0)
                ide_stats[ide]["loc_added"] += ide_data.get("loc_added_sum", 0)
        
        if not ide_stats:
            return ""
        
        rows = ""
        for ide, stats in sorted(ide_stats.items(), key=lambda x: x[1]["generations"], reverse=True):
            user_count = len(stats["users"])
            generations = stats["generations"]
            acceptances = stats["acceptances"]
            loc_added = stats["loc_added"]
            rate = (acceptances / generations * 100) if generations > 0 else 0
            
            rows += f"""
            <tr>
                <td><strong>{ide.upper()}</strong></td>
                <td>{user_count}</td>
                <td>{generations:,}</td>
                <td>{acceptances:,}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(rate, 100)}%">{rate:.1f}%</div>
                    </div>
                </td>
                <td>{loc_added:,}</td>
            </tr>
            """
        
        return f"""
        <h2>💻 IDE 使用统计</h2>
        <table>
            <thead>
                <tr>
                    <th>IDE</th>
                    <th>用户数</th>
                    <th>代码生成次数</th>
                    <th>代码接受次数</th>
                    <th>接受率</th>
                    <th>新增代码行数</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_language_stats_html(self) -> str:
        """生成编程语言统计的 HTML"""
        lang_stats = {}
        
        for record in self.data:
            for lang_data in record.get("totals_by_language_feature", []):
                lang = lang_data.get("language", "unknown")
                if lang == "unknown":
                    continue
                if lang not in lang_stats:
                    lang_stats[lang] = {
                        "generations": 0,
                        "acceptances": 0,
                        "loc_added": 0
                    }
                lang_stats[lang]["generations"] += lang_data.get("code_generation_activity_count", 0)
                lang_stats[lang]["acceptances"] += lang_data.get("code_acceptance_activity_count", 0)
                lang_stats[lang]["loc_added"] += lang_data.get("loc_added_sum", 0)
        
        if not lang_stats:
            return ""
        
        # 只显示前10个最常用的语言
        top_langs = sorted(lang_stats.items(), key=lambda x: x[1]["generations"], reverse=True)[:10]
        
        rows = ""
        for lang, stats in top_langs:
            generations = stats["generations"]
            acceptances = stats["acceptances"]
            loc_added = stats["loc_added"]
            rate = (acceptances / generations * 100) if generations > 0 else 0
            
            rows += f"""
            <tr>
                <td><strong>{lang}</strong></td>
                <td>{generations:,}</td>
                <td>{acceptances:,}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(rate, 100)}%">{rate:.1f}%</div>
                    </div>
                </td>
                <td>{loc_added:,}</td>
            </tr>
            """
        
        return f"""
        <h2>🔤 编程语言统计 (TOP 10)</h2>
        <table>
            <thead>
                <tr>
                    <th>编程语言</th>
                    <th>代码生成次数</th>
                    <th>代码接受次数</th>
                    <th>接受率</th>
                    <th>新增代码行数</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_feature_metrics(record: Dict[str, Any], feature_name: str) -> Dict[str, Any]:
        for feature in record.get("totals_by_feature", []):
            if feature.get("feature") == feature_name:
                return feature
        return {
            "feature": feature_name,
            "user_initiated_interaction_count": 0,
            "code_generation_activity_count": 0,
            "code_acceptance_activity_count": 0,
            "loc_suggested_to_add_sum": 0,
            "loc_suggested_to_delete_sum": 0,
            "loc_added_sum": 0,
            "loc_deleted_sum": 0,
        }

    @staticmethod
    def _sum_loc_added_from_ide(record: Dict[str, Any]) -> int:
        return sum(ide.get("loc_added_sum", 0) for ide in record.get("totals_by_ide", []))

    @staticmethod
    def _calculate_rate(numerator: float, denominator: float) -> float:
        if not denominator:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def export_all(self, output_dir: Path = None) -> None:
        """导出所有维度的 CSV 文件和 HTML 报告"""
        output_dir = Path(output_dir) if output_dir else self.json_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*80}")
        print(f"🚀 GitHub Copilot Metrics 数据导出")
        print(f"{'='*80}")
        print(f"📂 输出目录: {output_dir}")
        print(f"📅 数据期间: {self._get_date_range()}")
        print(f"👥 用户总数: {len(self.data)}")
        print(f"{'='*80}\n")

        base_name = self.json_file.stem
        files = []

        # 导出所有 CSV 文件
        print("📊 正在导出 CSV 文件...")
        files.append(self.export_user_summary(output_dir / f"{base_name}_user_summary.csv"))
        files.append(self.export_by_ide(output_dir / f"{base_name}_by_ide.csv"))
        files.append(self.export_by_feature(output_dir / f"{base_name}_by_feature.csv"))
        files.append(self.export_by_language_feature(output_dir / f"{base_name}_by_language_feature.csv"))
        files.append(self.export_by_language_model(output_dir / f"{base_name}_by_language_model.csv"))
        files.append(self.export_by_model_feature(output_dir / f"{base_name}_by_model_feature.csv"))
        files.append(self.export_code_completion_summary(output_dir / f"{base_name}_code_completion_summary.csv"))
        files.append(self.export_chat_loc_summary(output_dir / f"{base_name}_chat_loc_summary.csv"))

        # 导出 HTML 报告
        print("\n📊 正在生成 HTML 报告...")
        html_file = self.generate_html_report(output_dir / f"{base_name}_report.html")
        files.append(html_file)

        # 打印文件列表
        print(f"\n{'='*80}")
        print(f"✅ 导出完成！共生成 {len(files)} 个文件:")
        print(f"{'='*80}")
        for i, file in enumerate(files, 1):
            file_size = file.stat().st_size / 1024  # KB
            icon = "📄" if file.suffix == ".html" else "📊"
            print(f"   {icon} {i}. {file.name} ({file_size:.2f} KB)")
        print(f"{'='*80}\n")
        
        # 提示如何打开 HTML 报告
        print(f"💡 提示: 在浏览器中打开 {html_file.name} 查看可视化报告\n")

    def _write_csv(self, output_file: Path, headers: List[str], rows: List[Dict[str, Any]]) -> None:
        with output_file.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        print(f"   ✅ 已生成: {output_file} ({len(rows)} 行数据)")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GitHub Copilot User Level Metrics - JSON to CSV Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 json_to_csv.py input.json
  python3 json_to_csv.py input.json -o ./output
  python3 json_to_csv.py input.json -t code_completion_summary
        """,
    )

    parser.add_argument("json_file", help="输入的 JSON 文件路径")
    parser.add_argument("-o", "--output-dir", help="输出目录（可选）")
    parser.add_argument(
        "-t",
        "--type",
        choices=["user_summary", "all", "html"],
        default="all",
        help="导出的数据类型: user_summary(用户汇总CSV), all(所有CSV+HTML), html(仅HTML报告) [默认: all]",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    converter = CopilotMetricsConverter(args.json_file)

    output_dir = Path(args.output_dir) if args.output_dir else converter.json_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.type == "all":
        # 导出所有 CSV 文件和 HTML 报告
        converter.export_all(output_dir)
    elif args.type == "html":
        # 仅导出 HTML 报告
        html_file = converter.generate_html_report(output_dir / f"{converter.json_file.stem}_report.html")
        print(f"\n✅ HTML 报告已生成: {html_file}")
        print(f"💡 在浏览器中打开查看可视化报告\n")
    else:
        # 仅导出用户汇总 CSV
        converter.export_user_summary(output_dir / f"{converter.json_file.stem}_user_summary.csv")


if __name__ == "__main__":
    main()
