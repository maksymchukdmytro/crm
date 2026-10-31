"""Ключі налаштувань за розділами (що зберігає кожна вкладка «Налаштувань») і ключі-прапорці."""

SECTION_KEYS = {
    "fields": ["extra1_name", "extra2_name", "extra3_name", "extra4_name", "extra1_on", "extra2_on", "extra3_on", "extra4_on"],
    "checkbox": ["cb_sell_status", "cb_return_status", "cb_prepay_status", "cb_postpay_status"],
    "general": ["company_name", "duplicate_days", "auto_assign", "managers_see_own_only",
                "auto_status_from_tracking", "tracking_interval_min",
                "lead_wait_warn_min", "lead_wait_bad_min", "lead_noanswer_remind_min", "lead_to_order_status"],
    "np": ["np_api_key", "np_city_name", "np_city_ref", "np_warehouse_name", "np_warehouse_ref", "np_sender_phone",
           "np_cod_mode", "np_payer", "np_default_weight", "np_seat_size", "np_description", "np_sender_ref", "np_contact_ref"],
    "up": ["up_bearer", "up_token", "up_tracking_bearer", "up_sender_uuid", "up_sandbox", "up_type"],
    "meest": ["meest_username", "meest_password", "meest_sender_branch_id", "meest_sender_name", "meest_sender_phone"],
    "sms": ["sms_enabled", "sms_token", "sms_sender", "viber_sender"],
    "alerts": ["alert_tg_token", "alert_tg_chat", "alert_no_leads_hours"],
    "docs": ["doc_auto_issue", "doc_in_parcel", "doc_prefix", "invoice_prefix", "warranty_prefix", "doc_unit", "doc_accent", "doc_site", "doc_note", "doc_logo",
             "invoice_days", "warranty_months", "warranty_terms"],
}
CHECKBOXES = {"managers_see_own_only", "auto_status_from_tracking", "up_sandbox", "sms_enabled", "doc_in_parcel"}
