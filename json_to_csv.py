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
        output_dir = Path(output_dir) if output_dir else self.json_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n🚀 开始导出用户总体指标到目录: {output_dir}")
        print("=" * 72)

        output_file = self.export_user_summary(output_dir / f"{self.json_file.stem}_user_summary.csv")

        print("\n" + "=" * 72)
        print(f"✅ 导出完成！生成文件:")
        print(f"   📄 {output_file}")

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
        choices=["user_summary"],
        default="user_summary",
        help="导出的数据类型（默认: user_summary）",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    converter = CopilotMetricsConverter(args.json_file)

    output_dir = Path(args.output_dir) if args.output_dir else converter.json_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    converter.export_user_summary(output_dir / f"{converter.json_file.stem}_user_summary.csv")


if __name__ == "__main__":
    main()
