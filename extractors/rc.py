import re


class RCExtractor:

    def extract(self, text):

        result = {
            "document_type": "rc",
            "rc_number": None,
            "ice": None,
            "raw_text": text
        }

        # Recherche RC
        rc_patterns = [
            r"RC\s*[:\-]?\s*([0-9]{3,10})",
            r"REGISTRE\s+DE\s+COMMERCE\s*[:\-]?\s*([0-9]{3,10})"
        ]

        for pattern in rc_patterns:

            match = re.search(
                pattern,
                text.upper()
            )

            if match:

                result["rc_number"] = (
                    match.group(1)
                )

                break

        # Recherche ICE
        ice_pattern = (
            r"ICE\s*[:\-]?\s*([0-9]{10,20})"
        )

        match = re.search(
            ice_pattern,
            text.upper()
        )

        if match:

            result["ice"] = match.group(1)

        return result