# EXAMPLE OUTPUTS
output_example1 = {
    "borderSecurityFeature": "THE CHEQUE PAPER CONTAINS COLORED MICROPRINTING AND WATERMARK, PROTECTED BY THE LAW OF THE UNITED STATES",
    "payorName": "John Smith",
    "payorAddress": "313 carrie street, chattanooga, TN50301",
    "payToName": "Mary Johnson",
    "amountNumber": "10.35",
    "amountString": "ten and 35/100",
    "date": "2024-12-23",
    "serialNumber": "90",
    "routingNumber": "123456789",
    "accountNumber": "12345678",
    "bankName": "First State bank",
    "bankAddress": "All First State bank branches in USA"
}

output_example2 = {
    "license no": "3456789",
    "expires": "01/01/2025",
    "name and address": "test",
    "sex": "jkj",
    "hair": "fghjkl",
    "ht": "587",
    "wt": "567",
    "eyes": "uilkuy",
    "DOB": "01/01/2025",
    "signature": "yes"
}

output_example3 = {
    "Board of Directors or Sole Director": "LTIMindtree",
    "Laws of Country": "India",
    "Held at": "Mumbai",
    "On": "17th January 2025",
    "holder1": "john doe",
    "holder1_title": "Team Lead",
    "holder1_signature": "yes",
    "holder2": "jane doe",
    "holder2_title": "solution architect",
    "holder2_signature": "no",
    "Dated": "17th January 2025",
    "Printed Name,Title": "Mary Thomas"
}

output_example4 = {
    "LastName": "CRANWELL",
    "FirstAndMiddleName": "ANDREA CHARLOTTE",
    "Nationality": "BRITISH CITIZEN",
    "DateOfBirth": "1969-08-06",
    "PlaceOfBirth": "LINCOLN GBR",
    "Sex": "F",
    "CountryOfPassport": "GBR",
    "PassportDocumentNumber": "791234567",
    "IssueDate": "2009-05-31",
    "ExpirationDate": "2009-06-01",
    "IssuingAuthority": "FCO"
}

output_example5 = {
    "Account Name": "test",
    "Account Number": "123456",
    "Name of Stock": "test",
    "Social Security Number": "123456",
    "Undersigned": "test",
    "Residing at": "test",
    "Undersigned Role": "test",
    "Died on": "01/01/2025",
    "Residing at": "test",
    "Duration": "10",
    "Undersigned signature present": "no",
    "Sworn on":"01/01/2025",
    "Administer title":"test",
    "Administer signature present":"yes",
    "Commission expires on":"01/01/2025",
}

output_example6 = {
    "CertificateNumber": "ZQ00000000",
    "CompanyName": "iHeartMEDIA",
    "ShareholderName": "MR SAMPLE & MRS SAMPLE",
    "CUSIP": "45174J 60 8",
    "No of Shares": 000000,
    "PurchaseDate": "DD-MM-YYYY",
    "Class": "B",
    "Signatory 1":"Executive Vice President, General Counsel and Secretary",
    "Signatory 2":"Senior Vice President, Chief Accounting Officer and Assistant Secretary"
}

json_schema7 = {
    "borderSecurityFeature": {"type": "string", "description": "Security feature verbiage usually on top of a cheque, leave empty if doesn't exist"},
    "payorName": {"type": "string", "description": "Name of the person who is the one paying money"},
    "payorAddress": {"type": "string", "description": "Address of the person who is the one paying money"},
    "payToName": {"type": "string", "description": "Designates who can receive the money"},
    "amountNumber": {"type": "string", "description": "Displays the value of the check in numerical format and always display decimal part"},
    "amountString": {"type": "string", "description": "This is written out in a section using words instead of numbers"},
    "date": {"type": "string", "description": "Serves as a timestamp for the check"},
    "serialNumber": {"type": "string", "description": "This appears in two places and is a security measure to identify each payment and prevent fraud"},
    "routingNumber": {"type": "string", "description": "This tells banks where to find the funds for the check"},

    "accountNumber": {"type": "string", "description": "This is the identifier that lets the recipient know where the money for the check will come from"},

    # "amountSNComparison": {"type" "string"},
    "bankName": {"type": "string", "description": "Name of the bank printed on the check"},
    "bankAddress": {"type": "string", "description": "Address of the bank printed on the check"},


    
}

output_example7 = {
    "borderSecurityFeature": "THE CHEQUE PAPER CONTAINS COLORED MICROPRINTING AND WATERMARK, PROTECTED BY THE LAW OF THE UNITED STATES",
    "payorName": "John Smith",
    "payorAddress": "313 carrie street, chattanooga, TN50301",
    "payToName": "Mary Johnson",
    "amountNumber": "10.35",
    "amountString": "ten and 35/100",
    "date": "2024-12-23",
    "serialNumber": "90",
    "routingNumber": "123456789",
    "accountNumber": "12345678",
    "bankName": "First State bank",
    "bankAddress": "All First State bank branches in USA"
    
    # "amountSNComparison": "False"
}

chequeDataExample = {
    "borderSecurityFeature": "",
    "payorName": "",
    "payorAddress": "",
    "payToName": "",
    "amountNumber": "",
    "amountString": "",
    "date": "",
    "serialNumber": "",
    "routingNumber": "",
    "accountNumber": "",
    "bankName": "",
    "bankAddress": "",
    "age_in_days": "",
    "amountSNComparison": ""
}

result_format = {
    "comparison": "If the signatures are strictly of the same person return Pass otherwise return Fail. Only respond in Pass or Fail",
    "explanation": "explanation for the given signature comparison result"
}
result_example = {
    "comparison": "",
    "explanation": ""
}

out_ex_1 = [
                        {
                            "fitting number": "",
                            "qty": "null",
                            "part number": "RC12",
                            "d2 ring type": "",
                            "description": "12'' (304.8) DIA.- STAINLESS STEEL CAST RING",
                            "duct dia": 12,
                            "duct length": "null",
                            "confidence score": 95
                        },
                        {
                            "fitting number": "",
                            "qty": "null",
                            "part number": "RC14",
                            "d2 ring type": "",
                            "description": "14'' (355.6) DIA.- STAINLESS STEEL CAST RING",
                            "duct dia": 14,
                            "duct length": "null",
                            "confidence score": 95
                        }
                    ]

out_ex_2 = [
                        {
                            "fitting number": "KAZ-K061",
                            "qty": "2",
                            "part number": "RC04",
                            "d2 ring type": "H",
                            "description": "4 (101.6) DIA. - STAINLESS STEEL CAST RING",
                            "duct dia": "4",
                            "duct length": "",
                            "confidence score": 100
                        },
                        {
                            "fitting number": "KAM-M01",
                            "qty": "3",
                            "part number": "RC06",
                            "d2 ring type": "H",
                            "description": "6 (152.4) DIA. - STAINLESS STEEL CAST RING",
                            "duct dia": "6",
                            "duct length": "",
                            "confidence score": 100
                        }
                    ]