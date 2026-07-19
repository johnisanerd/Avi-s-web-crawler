import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.models import Lead
from src.config import Config
from src.constants import STANDARDIZED_COLUMNS, CLAY_COLUMNS
from src.logger import get_logger
from src.mappers import lead_to_standard_dict, lead_to_clay_lead, clay_lead_to_dict

logger = get_logger("exporter")


class LeadExporter:
    """
    Handles exporting collections of Lead records to multiple formats:
    Standardized CSV, Styled Excel, and Clay-ready CSV.
    """

    def __init__(self, config: Config):
        self.config = config

    def export_all(self, leads: List[Lead]) -> None:
        """
        Coordinates exporting lead data to all required formats in the target output directory.

        Args:
            leads: A list of Lead records.
        """
        logger.info(f"Initiating export for {len(leads)} unique leads...")
        
        # Ensure output directory exists before writing
        self.config.output_data_dir.mkdir(parents=True, exist_ok=True)

        csv_path = self.config.output_data_dir / self.config.cleaned_csv_name
        xlsx_path = self.config.output_data_dir / self.config.cleaned_xlsx_name
        clay_path = self.config.output_data_dir / self.config.clay_csv_name

        try:
            self._export_cleaned_csv(leads, csv_path)
            self._export_cleaned_xlsx(leads, xlsx_path)
            self._export_clay_csv(leads, clay_path)
            logger.info("All exports completed successfully.")
        except Exception as e:
            logger.error(f"Error occurred during file exports: {e}")
            raise

    def _export_cleaned_csv(self, leads: List[Lead], file_path: Path) -> None:
        """
        Exports standardized leads to CSV format.
        """
        logger.info(f"Exporting standard CSV to {file_path}...")
        mapped_data = [lead_to_standard_dict(lead) for lead in leads]
        
        df = pd.DataFrame(mapped_data)
        if df.empty:
            df = pd.DataFrame(columns=STANDARDIZED_COLUMNS)
        else:
            df = df[STANDARDIZED_COLUMNS]  # Enforce spec column order

        df.to_csv(file_path, index=False, encoding="utf-8")
        logger.info(f"CSV export success ({len(df)} rows written).")

    def _export_clay_csv(self, leads: List[Lead], file_path: Path) -> None:
        """
        Exports subset of leads configured for Clay imports to CSV format.
        """
        logger.info(f"Exporting Clay import CSV to {file_path}...")
        mapped_data = [clay_lead_to_dict(lead_to_clay_lead(lead)) for lead in leads]

        df = pd.DataFrame(mapped_data)
        if df.empty:
            df = pd.DataFrame(columns=CLAY_COLUMNS)
        else:
            df = df[CLAY_COLUMNS]  # Enforce spec column order

        df.to_csv(file_path, index=False, encoding="utf-8")
        logger.info(f"Clay CSV export success ({len(df)} rows written).")

    def _export_cleaned_xlsx(self, leads: List[Lead], file_path: Path) -> None:
        """
        Exports standardized leads to a styled Excel spreadsheet using openpyxl.
        """
        logger.info(f"Exporting styled Excel workbook to {file_path}...")
        mapped_data = [lead_to_standard_dict(lead) for lead in leads]

        df = pd.DataFrame(mapped_data)
        if df.empty:
            df = pd.DataFrame(columns=STANDARDIZED_COLUMNS)
        else:
            df = df[STANDARDIZED_COLUMNS]  # Enforce spec column order

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Brokerage Leads", index=False)
            
            workbook = writer.book
            worksheet = writer.sheets["Brokerage Leads"]
            
            # 1. Enable grid lines explicitly
            worksheet.views.sheetView[0].showGridLines = True

            # 2. Styling attributes
            theme_color = self.config.excel_theme_color
            header_fill = PatternFill(start_color=theme_color, end_color=theme_color, fill_type="solid")
            header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            
            zebra_fill = PatternFill(start_color="F2F6F9", end_color="F2F6F9", fill_type="solid")
            white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
            
            regular_font = Font(name="Segoe UI", size=10, bold=False, color="333333")
            link_font = Font(name="Segoe UI", size=10, bold=False, color=theme_color, underline="single")
            
            left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
            center_align = Alignment(horizontal="center", vertical="center")
            
            thin_border_side = Side(style="thin", color="D9D9D9")
            cell_border = Border(
                left=thin_border_side,
                right=thin_border_side,
                top=thin_border_side,
                bottom=thin_border_side
            )

            # 3. Apply header styling
            for col_idx in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_align
                cell.border = cell_border
                
            worksheet.row_dimensions[1].height = 28

            # 4. Apply data row styling
            for row_idx in range(2, len(df) + 2):
                worksheet.row_dimensions[row_idx].height = 22
                row_fill = zebra_fill if (row_idx % 2 == 0) else white_fill
                
                for col_idx, col_name in enumerate(df.columns, start=1):
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    cell.fill = row_fill
                    cell.font = regular_font
                    cell.border = cell_border
                    
                    # Apply specific alignments and formats depending on columns
                    if col_name in ["Rating", "Review Count", "State", "Zip Code", "Country"]:
                        cell.alignment = center_align
                        if col_name == "Rating":
                            cell.number_format = "0.0"
                        elif col_name == "Review Count":
                            cell.number_format = "#,##0"
                    elif col_name in ["Website", "Google Maps URL"]:
                        cell.alignment = left_align
                        if cell.value:
                            cell.font = link_font
                    else:
                        cell.alignment = left_align

            # 5. Enable auto-filters across columns
            worksheet.auto_filter.ref = worksheet.dimensions

            # 6. Freeze row pane below headers
            worksheet.freeze_panes = "A2"

            # 7. Auto-adjust column widths (bounded min=12, max=40)
            for col in worksheet.columns:
                max_len = 0
                for cell in col:
                    val_str = str(cell.value or "")
                    if len(val_str) > max_len:
                        max_len = len(val_str)
                col_letter = get_column_letter(col[0].column)
                calculated_width = min(max(max_len + 4, 12), 40)
                worksheet.column_dimensions[col_letter].width = calculated_width

        logger.info(f"Excel export success ({len(df)} rows written).")
