from ll.org.Export.Scripts.Resources import Resource as Rsc
from ll.org.Export.Scripts.Specs2Metadata import preVal, space
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from rdflib import Literal

RSC_SPACE = 0


class Validate:

    global RSC_SPACE
    TPL_SPACE = 2 + RSC_SPACE
    header = F"\n\n{'#' * 110}\n#{'VALIDATION TERMINOLOGY':^108}#\n{'#' * 110}\n\n"

    accepted = Rsc.ga_resource_ttl('Accepted')
    accepted_label = "Accepted"
    accepted_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as ACCEPTED. 
{space * TPL_SPACE}This, with the intent of notifying that the link has undergone and PASSED a user-defined set 
{space * TPL_SPACE}of checks which gives ground to CONFIRM the rightful creation of the context dependent link."""

    accepted_doc = F"""
{space * RSC_SPACE}### VALIDATED HAS ACCEPTED
{space * RSC_SPACE}{accepted}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, Literal(accepted_label).n3(), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(accepted_desc).n3(), line=False, end=True)}
    """

    rejected = Rsc.ga_resource_ttl('Rejected')
    rejected_label = "Rejected"
    rejected_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as REJECTED. 
{space * TPL_SPACE}This, with the intent of notifying that the link has undergone and FAILED a user-defined 
{space * TPL_SPACE}set of checks which gives ground to REFUTE the creation of the context dependent link."""

    rejected_doc = F"""
{space * RSC_SPACE}### VALIDATED HAS REJECTED
{space * RSC_SPACE}{rejected}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, Literal(rejected_label).n3(), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(rejected_desc).n3(), line=False, end=True)}
    """

    unsure = Rsc.ga_resource_ttl('Unsure')
    unsure_label = "Uncertain"
    unsure_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as UNSURE. 
{space * TPL_SPACE}This flag reveals the the lack of confidence in confirming or refuting the creation 
{space * TPL_SPACE}of the context dependent link."""

    unsure_doc = F"""
{space * RSC_SPACE}### VALIDATED HAS UNSURE
{space * RSC_SPACE}{unsure}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, Literal(unsure_label).n3(), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(unsure_desc).n3(), line=False, end=True)}
    """

    unchecked = Rsc.ga_resource_ttl('Unchecked')
    unchecked_label = "Unchecked"
    unchecked_desc = F"""
{space * TPL_SPACE}Flagging a link as UNCHECKED literally highlights that it has not undergone any user-defined scrutiny 
{space * TPL_SPACE}such that it could be flagged as ACCEPTED, REJECTED or UNSURE"""

    unchecked_doc = F"""
{space * RSC_SPACE}### VALIDATED HAS UNSURE
{space * RSC_SPACE}{unchecked}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, Literal(unchecked_label).n3(), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(unchecked_desc).n3(), line=False, end=True)}
    """

    get_resource = {
        'accepted': accepted,
        'rejected': rejected,
        'not_sure': unsure,
        'not_validated': unchecked,
    }

    get_triples = {
        'accepted': accepted_doc,
        'rejected': rejected_doc,
        'not_sure': unchecked_doc,
        'not_validated': unchecked_doc,
    }

    def terminology(self):

        return F"{self.header}" \
               F"{self.accepted_doc}" \
               F"{self.rejected_doc}" \
               F"{self.unchecked_doc}" \
               F"{self.unchecked_doc}"

