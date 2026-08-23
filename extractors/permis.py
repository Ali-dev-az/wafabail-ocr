import re


class PermisExtractor:

    def extract(self, text):

        result = {
            "document_type": "permis",
            "license_number": None,
            "raw_text": text
        }

        patterns = [
            r"\b[A-Z]{1,3}\s?[0-9]{4,10}\b",
            r"\b[0-9]{6,12}\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text.upper()
            )

            if match:

                result["license_number"] = (
                    match.group(0)
                    .replace(" ", "")
                )

                break

        return result