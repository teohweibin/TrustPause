"""Instant template texts for paused / held transfers.

Shown straight away; Granite (card 05) replaces them when its text is ready.
The Bahasa Malaysia wording should be checked by a native speaker.
"""

# Short Bahasa Malaysia versions of the reason codes in src/reasons.py
REASONS_BM = {
    "RECEIVER_REPORTED": lambda n: "akaun penerima dikaitkan dengan kes yang pernah dilaporkan",
    "RECEIVER_PAID_BY_REPORTED": lambda n: f"akaun penerima menerima wang daripada {n} akaun yang dilaporkan dalam 24 jam lalu",
    "RECEIVER_PAYS_REPORTED": lambda n: f"akaun penerima menghantar wang kepada {n} akaun yang dilaporkan dalam 24 jam lalu",
    "FAN_IN_HIGH": lambda n: f"akaun penerima menerima wang daripada {n} penghantar berbeza dalam 24 jam lalu",
    "RECEIVER_BURST": lambda n: f"akaun penerima menerima {n} pemindahan dalam sejam lalu",
    "RECEIVER_VOLUME": lambda n: f"akaun penerima menerima {n} pemindahan dalam 24 jam lalu",
    "NEW_RECIPIENT": lambda n: "ini penerima baharu bagi anda",
    "NEW_ACCOUNT": lambda n: "akaun penerima masih baharu",
    "FEW_PAST_RECEIPTS": lambda n: "akaun penerima jarang menerima wang sebelum ini",
    "AMOUNT_UNUSUAL": lambda n: "jumlah ini luar biasa bagi akaun penerima",
}
GENERIC_BM = "corak pembayaran ini sering dilihat dalam kes penipuan"


def _join(parts, word):
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + f" {word} " + parts[-1]


def _bm(reason):
    builder = REASONS_BM.get(reason["code"])
    return builder(int(round(reason["value"]))) if builder else GENERIC_BM


def template_texts(decision, score, reasons, sender_reasons):
    """Return warning_en, warning_bm (for the sender) and analyst_note."""
    top = sender_reasons[:2]
    why_en = _join([r["sentence"] for r in top], "and") or "this payment matches patterns seen in scams"
    why_bm = _join(list(dict.fromkeys(_bm(r) for r in top)), "dan") or GENERIC_BM
    why_en = why_en[0].upper() + why_en[1:]
    why_bm = why_bm[0].upper() + why_bm[1:]

    if decision == "hold":
        warning_en = (f"This transfer is on hold while our team checks it, to protect you. {why_en}. "
                      "No money has left your account yet.")
        warning_bm = (f"Pemindahan ini ditahan sementara pasukan kami menyemaknya, untuk melindungi anda. {why_bm}. "
                      "Tiada wang telah keluar dari akaun anda lagi.")
    else:
        warning_en = (f"Wait, please check this recipient before sending. {why_en}. "
                      "Scammers often rush people into paying. If someone contacted you unexpectedly, cancel this transfer.")
        warning_bm = (f"Tunggu sebentar, sila semak penerima ini sebelum menghantar. {why_bm}. "
                      "Penipu sering mendesak mangsa supaya membayar segera. Jika anda dihubungi tanpa diduga, batalkan pemindahan ini.")

    evidence = "; ".join(r["sentence"] for r in reasons) or "no single dominant signal"
    action = "Hold and verify the receiving account before release." if decision == "hold" \
        else "Monitor; sender has been warned and must confirm."
    analyst_note = (f"- Pattern: {decision.upper()}, risk score {score:.3f}\n"
                    f"- Evidence: {evidence}\n"
                    f"- Suggested action: {action}")
    return {"warning_en": warning_en, "warning_bm": warning_bm, "analyst_note": analyst_note}
