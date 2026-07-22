import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli.console import Console
    from src.models import Lead


class PipelineProgressTracker:
    """
    Manages live status updates during single or multi-lead pipeline execution.
    Displays step-by-step active stages with live details.
    """

    STAGES = [
        ("Discovering website", "Scanning target URL and checking domain connectivity"),
        ("Crawling pages", "Extracting page content, text blocks, and links"),
        ("Business Intelligence", "Profiling agent count, offices, and business model"),
        ("Decision Maker Intelligence", "Identifying owners, executives, and verified emails"),
        ("Revenue Intelligence", "Estimating deal volume, transaction counts, and GCI"),
        ("Technology Intelligence", "Detecting CMS, IDX, CRM, and analytics stack"),
        ("Lead Scoring", "Calculating priority score and tier classification")
    ]

    def __init__(self, console: "Console"):
        self.console = console
        self.total_stages = len(self.STAGES)

    def start_stage(self, stage_num: int, name: str) -> None:
        prefix = f"[{stage_num}/{self.total_stages}]"
        msg = f"{self.console.SYM_BULLET} {prefix} {name}..."
        if self.console.rich_available:
            self.console.print(f"[cyan]{msg}[/cyan]")
        else:
            print(msg)

    def complete_stage(self, stage_num: int, name: str, detail: Optional[str] = None) -> None:
        prefix = f"[{stage_num}/{self.total_stages}]"
        detail_str = f" ({detail})" if detail else ""
        msg = f"{self.console.SYM_SUCCESS} {prefix} {name}{detail_str}"
        if self.console.rich_available:
            self.console.print(f"[success]{msg}[/success]")
        else:
            print(msg)

    def fail_stage(self, stage_num: int, name: str, reason: str) -> None:
        prefix = f"[{stage_num}/{self.total_stages}]"
        msg = f"{self.console.SYM_ERROR} {prefix} {name} (Failed: {reason})"
        if self.console.rich_available:
            self.console.print(f"[error]{msg}[/error]")
        else:
            print(msg)


def render_lead_result(console: "Console", lead: "Lead", proc_time_ms: float = 0.0) -> None:
    """
    Renders structured lead result panel/table cleanly.
    """
    dm_name = lead.owner_name or (lead.decision_maker.decision_maker_name if lead.decision_maker else None) or "Not Found"
    dm_title = lead.owner_title or (lead.decision_maker.decision_maker_title if lead.decision_maker else None) or "N/A"
    dm_email = lead.owner_email or lead.business_email or (lead.decision_maker.verified_email if lead.decision_maker else None) or "Unverified"
    
    rev_str = "N/A"
    if lead.estimated_revenue_low and lead.estimated_revenue_high:
        rev_str = f"${lead.estimated_revenue_low:,.0f} - ${lead.estimated_revenue_high:,.0f}"
    elif lead.estimated_gci:
        rev_str = f"${lead.estimated_gci:,.0f} GCI"

    tech_stack = []
    if lead.cms: tech_stack.append(f"CMS: {lead.cms}")
    if lead.idx_provider: tech_stack.append(f"IDX: {lead.idx_provider}")
    if lead.crm_platform: tech_stack.append(f"CRM: {lead.crm_platform}")
    tech_str = ", ".join(tech_stack) if tech_stack else "Standard HTML"

    conf = lead.business_intelligence_confidence or "Medium"

    if console.rich_available:
        content = f"""[bold cyan]Business Name[/bold cyan]       {lead.business_name}
[bold cyan]Website[/bold cyan]             {lead.website or 'N/A'}
[bold cyan]Decision Maker[/bold cyan]      {dm_name} ({dm_title})
[bold cyan]Verified Email[/bold cyan]      {dm_email}
[bold cyan]Estimated Revenue[/bold cyan]   {rev_str}
[bold cyan]Technology Stack[/bold cyan]    {tech_str}
[bold cyan]Lead Score[/bold cyan]          [bold green]{lead.lead_score}/100[/bold green] ({lead.lead_tier})
[bold cyan]Confidence[/bold cyan]          {conf}
[bold cyan]Processing Time[/bold cyan]     {proc_time_ms:.1f} ms"""

        console.print_panel(
            content,
            title=f"Crawl Result: {lead.business_name}",
            style="green" if lead.lead_score >= 70 else "blue"
        )
    else:
        console.print(f"\n=================== CRAWL RESULT: {lead.business_name} ===================")
        console.print(f"Business           : {lead.business_name}")
        console.print(f"Website            : {lead.website}")
        console.print(f"Decision Maker     : {dm_name} ({dm_title})")
        console.print(f"Verified Email     : {dm_email}")
        console.print(f"Estimated Revenue  : {rev_str}")
        console.print(f"Technology Stack   : {tech_str}")
        console.print(f"Lead Score         : {lead.lead_score}/100 ({lead.lead_tier})")
        console.print(f"Confidence         : {conf}")
        console.print(f"Processing Time    : {proc_time_ms:.1f} ms")
        console.print("=========================================================================\n")
