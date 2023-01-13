if .schemas | index("urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101") == null 
	then 
		.schemas |= . + ["urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101"] 
	else 
		. 
end
|
if ."urn:mace:oclc.org:eidm:schema:persona:wmscircpatroninfo:20180101".circulationInfo.borrowerCategory == "UQTR - Communauté uni. BUQ"
	then
		."urn:mace:oclc.org:eidm:schema:persona:persona:20180305".oclcExpirationDate 
			= "2039-06-29T00:00:00Z"
		| ."urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101".illInfo.illPatronType 
			= "Employés" 
	else
		."urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101".illInfo.illPatronType =
			(."urn:mace:oclc.org:eidm:schema:persona:additionalinfo:20180501".oclcKeyValuePairs[] | select(.key = "customdata1") | .value)
end
| ."urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101".illInfo.illId 
	= ."urn:mace:oclc.org:eidm:schema:persona:wmscircpatroninfo:20180101".circulationInfo.barcode 
| ."urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101".illInfo.isBlocked 
	= true 
| ."urn:mace:oclc.org:eidm:schema:persona:wsillinfo:20180101".illInfo.isApproved
	= false