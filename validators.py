"""
=========================================================
WAFABAIL
Document Validator
=========================================================
"""

import re


class DocumentValidator:

    def __init__(self):
        pass

    # =====================================================
    # VALIDATION CIN
    # =====================================================

    def validate_cin(self, data):

        errors = []
        warnings = []

        cin_number = data.get("cin_number")

        if not cin_number:

            errors.append(
                "Numéro CIN non détecté"
            )

        else:

            cin_number = str(
                cin_number
            ).upper().replace(
                " ",
                ""
            )

            # Format marocain courant :
            # 1 à 3 lettres + chiffres

            if not re.fullmatch(
                r"[A-Z]{1,3}\d{4,8}",
                cin_number
            ):

                warnings.append(
                    "Format du numéro CIN inhabituel"
                )

        # -------------------------------------------------
        # Informations facultatives
        # -------------------------------------------------

        if not data.get("name"):

            warnings.append(
                "Nom non détecté"
            )

        if not data.get("surname"):

            warnings.append(
                "Prénom non détecté"
            )

        if not data.get("birth_date"):

            warnings.append(
                "Date de naissance non détectée"
            )

        # -------------------------------------------------
        # VALIDITE
        # -------------------------------------------------

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings
        }

    # =====================================================
    # VALIDATION PASSPORT
    # =====================================================

    def validate_passport(self, data):

        errors = []
        warnings = []

        passport_number = data.get(
            "passport_number"
        )

        if not passport_number:

            errors.append(
                "Numéro de passeport non détecté"
            )

        else:

            passport_number = str(
                passport_number
            ).upper().replace(
                " ",
                ""
            )

            if not re.fullmatch(
                r"[A-Z]{1,2}\d{6,8}",
                passport_number
            ):

                warnings.append(
                    "Format du numéro de passeport inhabituel"
                )

        if not data.get(
            "nationality"
        ):

            warnings.append(
                "Nationalité non détectée"
            )

        if not data.get(
            "birth_date"
        ):

            warnings.append(
                "Date de naissance non détectée"
            )

        return {

            "valid":
                len(errors) == 0,

            "errors":
                errors,

            "warnings":
                warnings
        }

    # =====================================================
    # VALIDATION PERMIS
    # =====================================================

    def validate_permis(self, data):

        errors = []
        warnings = []

        number = data.get(
            "license_number"
        )

        if not number:

            errors.append(
                "Numéro de permis non détecté"
            )

        if not data.get(
            "name"
        ):

            warnings.append(
                "Nom non détecté"
            )

        return {

            "valid":
                len(errors) == 0,

            "errors":
                errors,

            "warnings":
                warnings
        }

    # =====================================================
    # VALIDATION RC
    # =====================================================

    def validate_rc(self, data):

        errors = []
        warnings = []

        rc_number = data.get(
            "rc_number"
        )

        if not rc_number:

            errors.append(
                "Numéro RC non détecté"
            )

        if not data.get(
            "company_name"
        ):

            warnings.append(
                "Nom de société non détecté"
            )

        return {

            "valid":
                len(errors) == 0,

            "errors":
                errors,

            "warnings":
                warnings
        }

    # =====================================================
    # VALIDATION PRINCIPALE
    # =====================================================

    def validate(
        self,
        document_type,
        data
    ):

        document_type = str(
            document_type
        ).lower().strip()

        if document_type == "cin":

            return self.validate_cin(
                data
            )

        elif document_type == "passport":

            return self.validate_passport(
                data
            )

        elif document_type == "permis":

            return self.validate_permis(
                data
            )

        elif document_type == "rc":

            return self.validate_rc(
                data
            )

        return {

            "valid": False,

            "errors": [
                "Type de document inconnu"
            ],

            "warnings": []

        }