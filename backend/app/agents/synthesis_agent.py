import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("pmc_chatbot.agents.synthesis")


class SynthesisAgent:
    """Specialized Agent for Executive Markdown Report Card Generation & Summary Insights."""

    @classmethod
    def generate_report(
        cls,
        query_text: str,
        sql_used: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        is_marathi: bool = False,
        unresolved_entities: Optional[List[str]] = None
    ) -> str:
        """Formats tabular database query results into executive Markdown report cards."""
        lines = []

        if unresolved_entities:
            terms_str = ", ".join([f'**"{t}"**' for t in unresolved_entities])
            if is_marathi:
                lines.append(f"> ℹ️ **टीप:** {terms_str} नावाचा कोणताही विभाग/क्षेत्रीय कार्यालय/वर्ग महापालिकेच्या मुख्य नोंदवहीत आढळला नाही. खालील आकडेवारी सर्वसाधारण आहे.\n")
            else:
                lines.append(f"> ℹ️ **Notice:** No PMC department, ward, or category matching {terms_str} was found in master records. Displaying general complaint statistics below.\n")

        if not data:
            if is_marathi:
                lines.append("### ℹ️ माहिती\n\nदिलेल्या शोधासाठी कोणतीही प्रलंबित/माहिती नोंदी आढळल्या नाहीत.")
            else:
                lines.append("### ℹ️ Analytics Result\n\nNo records found matching the specified criteria.")
            return "\n".join(lines)

        # Filter out _mar columns from header display if duplicate
        display_cols = [c for c in columns if not c.endswith("_mar")]
        if not display_cols:
            display_cols = columns

        # 1. Total counts computation
        count_cols = [
            c for c in display_cols
            if any(k in c.lower() for k in ['received', 'total', 'count', 'pending', 'resolved', 'assigned', 'breached', 'open', 'complaints'])
        ]
        primary_num_col = count_cols[0] if count_cols else None

        if primary_num_col:
            total_sum = sum(
                row.get(primary_num_col, 0)
                for row in data
                if isinstance(row.get(primary_num_col), (int, float))
            )
            formatted_num = f"{total_sum:,}"
            num_label = primary_num_col.replace("_", " ").title()
            if is_marathi:
                lines.append(f"### 📊 एकूण {num_label}: **{formatted_num}**\n")
            else:
                lines.append(f"### 📊 Total {num_label}: **{formatted_num}**\n")

        # 2. Markdown Table Formatting
        headers = " | ".join([c.replace("_", " ").title() for c in display_cols])
        divider = " | ".join(["---"] * len(display_cols))
        lines.append(f"| {headers} |")
        lines.append(f"| {divider} |")

        for row in data:
            row_vals = []
            for c in display_cols:
                v = row.get(c, "")
                if isinstance(v, (int, float)):
                    row_vals.append(f"{v:,}")
                else:
                    v_str = str(v or "").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("|", "╱").strip()
                    row_vals.append(v_str if v_str else "-")
            lines.append("| " + " | ".join(row_vals) + " |")

        lines.append("\n---")

        # 3. Executive Insight Synthesis
        dim_cols = [
            c for c in display_cols
            if not any(k in c.lower() for k in ['month', 'date', 'time', 'year', 'created', 'id', 'pct', 'rate', 'percentage'])
            and not isinstance(data[0].get(c), (int, float))
        ]

        if primary_num_col and data:
            max_row = max(data, key=lambda r: (r.get(primary_num_col) or 0) if isinstance(r.get(primary_num_col), (int, float)) else 0)
            max_val = max_row.get(primary_num_col)

            if dim_cols:
                top_dim_col = dim_cols[0]
                top_name = str(max_row.get(top_dim_col, "-"))
                if top_name and top_name != "-":
                    if is_marathi:
                        lines.append(f"> 💡 **कार्यकारी निष्कर्ष:** सर्वात जास्त प्रमाण **{top_name}** ({max_val:,} तक्रारी) मध्ये नोंदवले गेले आहे.\n")
                    else:
                        lines.append(f"> 💡 **Executive Insight:** Highest volume recorded under **{top_name}** ({max_val:,} complaints).\n")

        return "\n".join(lines)
