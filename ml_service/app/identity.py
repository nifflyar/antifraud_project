"""Identity consistency features for detecting document/name mismatches."""

from typing import Dict, Tuple
import pandas as pd


def build_identity_consistency_features(
    transactions_df: pd.DataFrame,
) -> Dict[str, Dict]:
    """
    Build identity consistency features from transactions.

    Detects patterns like:
    - Same IIN used with multiple different FIOs
    - Same document number with multiple FIOs
    - Same FIO with multiple IINs
    - Missing identity info

    Args:
        transactions_df: DataFrame with columns: passenger_id, iin, doc_no, fio_clean

    Returns:
        Dict[passenger_id] -> {
            'same_iin_multiple_fio': int (count of distinct FIOs),
            'same_doc_multiple_fio': int,
            'same_fio_multiple_iin': int,
            'same_fio_multiple_doc': int,
            'missing_identity_flag': bool,
            'consistency_risk_score': float (0-100),
            'consistency_issues': list of strings
        }
    """

    consistency_data: Dict[str, Dict] = {}

    # Build IIN->FIO mappings
    iin_to_fios: Dict[str, set] = {}
    doc_to_fios: Dict[str, set] = {}
    fio_to_iins: Dict[str, set] = {}
    fio_to_docs: Dict[str, set] = {}

    for _, row in transactions_df.iterrows():
        pid = str(row.get("passenger_id", "unknown"))
        iin = row.get("iin")
        doc_no = row.get("doc_no")
        fio_clean = row.get("fio_clean")

        if iin and fio_clean:
            if iin not in iin_to_fios:
                iin_to_fios[iin] = set()
            iin_to_fios[iin].add(fio_clean)

        if doc_no and fio_clean:
            if doc_no not in doc_to_fios:
                doc_to_fios[doc_no] = set()
            doc_to_fios[doc_no].add(fio_clean)

        if fio_clean and iin:
            if fio_clean not in fio_to_iins:
                fio_to_iins[fio_clean] = set()
            fio_to_iins[fio_clean].add(iin)

        if fio_clean and doc_no:
            if fio_clean not in fio_to_docs:
                fio_to_docs[fio_clean] = set()
            fio_to_docs[fio_clean].add(doc_no)

    # Build per-passenger consistency features
    for _, row in transactions_df.iterrows():
        pid = str(row.get("passenger_id", "unknown"))
        if pid in consistency_data:
            continue  # Already computed

        iin = row.get("iin")
        doc_no = row.get("doc_no")
        fio_clean = row.get("fio_clean")

        same_iin_fios = len(iin_to_fios.get(iin, set())) if iin else 0
        same_doc_fios = len(doc_to_fios.get(doc_no, set())) if doc_no else 0
        same_fio_iins = len(fio_to_iins.get(fio_clean, set())) if fio_clean else 0
        same_fio_docs = len(fio_to_docs.get(fio_clean, set())) if fio_clean else 0

        risk_score = 0.0
        issues = []

        # Score: Same IIN with 3+ different FIOs is very suspicious
        if same_iin_fios >= 4:
            risk_score += 25
            issues.append(f"same_iin_multiple_fio:{same_iin_fios}")
        elif same_iin_fios >= 3:
            risk_score += 15
            issues.append(f"same_iin_multiple_fio:{same_iin_fios}")
        elif same_iin_fios == 2:
            risk_score += 5
            issues.append(f"same_iin_two_fios")

        # Score: Same document with 3+ different FIOs
        if same_doc_fios >= 4:
            risk_score += 20
            issues.append(f"same_doc_multiple_fio:{same_doc_fios}")
        elif same_doc_fios >= 3:
            risk_score += 12
            issues.append(f"same_doc_multiple_fio:{same_doc_fios}")

        # Score: Common FIO with 3+ different IINs (high because common names are common)
        if same_fio_iins >= 5:
            risk_score += 15
            issues.append(f"same_fio_multiple_iin:{same_fio_iins}")
        elif same_fio_iins >= 3:
            risk_score += 8
            issues.append(f"same_fio_multiple_iin:{same_fio_iins}")

        # Score: FIO with 3+ different documents
        if same_fio_docs >= 4:
            risk_score += 15
            issues.append(f"same_fio_multiple_doc:{same_fio_docs}")
        elif same_fio_docs >= 3:
            risk_score += 10
            issues.append(f"same_fio_multiple_doc:{same_fio_docs}")

        # Missing identity is risky
        if not iin and not doc_no:
            risk_score += 8
            issues.append("missing_identity_info")

        # Only IIN or only document is less risky but still notable
        if (iin and not doc_no) or (doc_no and not iin):
            risk_score += 3
            issues.append("single_identity_type")

        consistency_data[pid] = {
            "same_iin_multiple_fio": same_iin_fios,
            "same_doc_multiple_fio": same_doc_fios,
            "same_fio_multiple_iin": same_fio_iins,
            "same_fio_multiple_doc": same_fio_docs,
            "missing_identity_flag": not iin and not doc_no,
            "consistency_risk_score": min(100.0, risk_score),
            "consistency_issues": issues[:3],  # Top 3 issues
        }

    return consistency_data
