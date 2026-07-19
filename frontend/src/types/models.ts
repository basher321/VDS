export interface Issuer {
  id: number; name: string; address?: string | null; bin?: string | null;
  is_default: boolean; officer_name?: string | null; officer_designation?: string | null;
  officer_email?: string | null; default_bank_name?: string | null; default_description?: string | null;
}
export interface Signature {
  id: number; name: string; designation?: string | null; email?: string | null; enabled: boolean;
  image_path?: string | null;
}
export interface Numbering {
  id?: number; issuer_id?: number; company_token: string; fiscal_year_format: string;
  separator: string; pad_width: number; start_number: number; reset_policy: string; number_format: string;
}
export interface Rate {
  id: number; category_code: string; description: string; vds_rate: number;
  base_rule: string; effective_from: string; effective_to?: string | null;
}
export interface OrgSettings {
  smtp_host?: string; smtp_port?: number; smtp_user?: string; smtp_from?: string;
  smtp_use_tls?: boolean; wa_provider?: string; wa_phone_number_id?: string;
  wa_twilio_sid?: string; wa_twilio_from?: string; dispatch_mode?: string;
}
export interface PendingGroup {
  supplier_id: number; supplier: string; bin?: string | null; period: string;
  line_count: number; total_incl: number; total_vat: number;
}
export interface Certificate {
  id: number; certificate_no: string; supplier: string; bin?: string | null; period: string;
  issue_date: string; issue_date_mode: string; total_value_incl: number; total_vat: number;
  total_withheld: number; has_bin: boolean; remarks?: string | null; status: string;
}
export interface ImportRow {
  excel_row: number; supplier_name: string; supplier_bin: string; treasury_challan_no: string;
  category: string; deducted_vat?: number | null; vat_rate?: number | null;
  value_excl?: number | null; value_incl?: number | null; error?: string | null;
}
export interface ImportResult {
  batch_id: number; filename: string; total_rows: number; ok_rows: number;
  error_rows: number; rows: ImportRow[];
}
export interface DashboardData {
  imported_lines: number; suppliers: number; pending_groups: number; queued_dispatches: number;
  total_vat_withheld: number; certificates: { generated: number; sent: number };
}
export interface Anomaly { code: string; message: string; }
export interface DispatchJob { id: number; channel: string; recipient: string; status: string; opened_at?: string | null; }
