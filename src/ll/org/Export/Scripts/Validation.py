from ll.org.Export.Scripts.Resources import Resource as Rsc
from ll.org.Export.Scripts.Specs2Metadata import preVal, space
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from rdflib import Literal, Graph
from ll.org.Export.Scripts.VoidPlus import VoidPlus
import ll.org.Export.Scripts.Variables as Vars
MANAGER = Graph().namespace_manager

RSC_SPACE = 0


def valueList(objects, padding=1, newLine=True):
    if newLine:
        return F" ,\n{space * padding}{' ' * Vars.PRED_SIZE}".join(Literal(elt).n3(MANAGER) for elt in objects)
    else:
        return F", ".join(Literal(elt).n3(MANAGER) for elt in objects)


def header(message, lines=2):
    liner = "\n"
    return F"{liner * lines}{'#' * 80:^110}\n{' ' * 15}#{message:^78}#\n{'#' * 80:^110}{liner * (lines - 1)}\n"


class Validate:

    global RSC_SPACE
    TPL_SPACE = 2 + RSC_SPACE
    # header = F"\n\n{'#' * 110}\n#{'VALIDATION TERMINOLOGY':^108}#\n{'#' * 110}\n\n"

    # -------------------------------------- #
    # ACCEPTED
    # -------------------------------------- #
    accepted = Rsc.ga_resource_ttl('Accepted')
    accepted_label = "Accepted"
    accepted_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as ACCEPTED. 
{space * TPL_SPACE}This, with the intent of notifying that the link has undergone and PASSED a user-defined set 
{space * TPL_SPACE}of checks which gives ground to CONFIRM the rightful creation of the context dependent link."""
    accepted_doc = F"""
{space * RSC_SPACE}### VALIDATED AS ACCEPTED
{space * RSC_SPACE}{accepted}
    {space * RSC_SPACE}{preVal('a', VoidPlus.ValidationFlag_ttl, line=False)}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, Literal(accepted_label).n3(), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(accepted_desc).n3(), line=False, end=True)}
    """

    # -------------------------------------- #
    # REJECTED
    # -------------------------------------- #
    rejected = Rsc.ga_resource_ttl('Rejected')
    rejected_label = ["Not Accepted", "Rejected"]
    rejected_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as REJECTED. 
{space * TPL_SPACE}This, with the intent of notifying that the link has undergone and FAILED a user-defined 
{space * TPL_SPACE}set of checks which gives ground to REFUTE the creation of the context dependent link."""
    rejected_doc = F"""
{space * RSC_SPACE}### VALIDATED AS REJECTED
{space * RSC_SPACE}{rejected}
    {space * RSC_SPACE}{preVal('a', VoidPlus.ValidationFlag_ttl, line=False)}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, valueList(rejected_label, newLine=False), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(rejected_desc).n3(), line=False, end=True)}
    """

    # -------------------------------------- #
    # UNCERTAIN - NOT SURE
    # -------------------------------------- #
    unsure = Rsc.ga_resource_ttl('Uncertain')
    unsure_label = ["Not Sure", "Unsure", "Uncertain"]
    unsure_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as UNCERTAIN. 
{space * TPL_SPACE}This flag reveals the lack of confidence in confirming or refuting the creation of
{space * TPL_SPACE}the context dependent link."""
    unsure_doc = F"""
{space * RSC_SPACE}### VALIDATED AS UNCERTAIN
{space * RSC_SPACE}{unsure}
    {space * RSC_SPACE}{preVal('a', VoidPlus.ValidationFlag_ttl, line=False)}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, valueList(unsure_label, newLine=False), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(unsure_desc).n3(), line=False, end=True)}
    """

    # -------------------------------------- #
    # UNCHECKED - NOT VALIDATED
    # -------------------------------------- #
    unchecked = Rsc.ga_resource_ttl('Unchecked')
    unchecked_label = ["Not Validated", "Not Checked", "Unchecked"]
    unchecked_desc = F"""
{space * TPL_SPACE}Flagging a link as UNCHECKED literally highlights that it has not undergone any user-defined scrutiny 
{space * TPL_SPACE}such that it could be flagged as ACCEPTED, REJECTED or UNCERTAIN"""
    unchecked_doc = F"""
{space * RSC_SPACE}### VALIDATED AS UNCHECKED
{space * RSC_SPACE}{unchecked}
    {space * RSC_SPACE}{preVal('a', VoidPlus.ValidationFlag_ttl, line=False)}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, valueList(unchecked_label, newLine=False), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(unchecked_desc).n3(), line=False, end=True)}
    """

    # -------------------------------------- #
    # MIXED - DISPUTED - CONTRADICTION
    # -------------------------------------- #
    mixed = Rsc.ga_resource_ttl('Disputed')
    mixed_label = ["Contradictory", "Disputed"]
    mixed_desc = F"""
{space * TPL_SPACE}A validation process that results in the link under scrutiny being flagged as DISPUTED.  
{space * TPL_SPACE}This, with the intent of notifying that the link has undergone MULTIPLE user-defined set of checks
{space * TPL_SPACE}which result in a contradiction. In other words, the same link has been flagged with contradicting
{space * TPL_SPACE}labels such as for example ACCEPTED, ACCEPTED, UNSURE AND UNCHECKED"""
    mixed_doc = F"""
{space * RSC_SPACE}### VALIDATED AS DISPUTED
{space * RSC_SPACE}{mixed}
    {space * RSC_SPACE}{preVal('a', VoidPlus.ValidationFlag_ttl, line=False)}
    {space * RSC_SPACE}{preVal(Sns.RDFS.label_ttl, valueList(mixed_label, newLine=False), line=False)}
    {space * RSC_SPACE}{preVal(Sns.DCterms.description_ttl, Literal(mixed_desc).n3(), line=False, end=True)}
        """

    generic_desc = F"""
{space * TPL_SPACE}Unless explicitly stated in a specific validation resource, 
{space * TPL_SPACE}a. An accepted link entails that the validator agrees with the alignment (matching) in general and 
{space * TPL_SPACE}with the specific correspondence under scrutiny.
{space * TPL_SPACE}b. A rejected link entails that the validator agrees with the alignment (matching) in general but 
{space * TPL_SPACE}disagrees with the specific correspondence under scrutiny. Together, the values of the selected 
{space * TPL_SPACE}properties provided by the validator justify her disagreement.
{space * TPL_SPACE}c. Rejecting an alignment entails that the validator disagrees with the alignment in general and 
{space * TPL_SPACE}may have selected a set of properties for which the values justify her disagreement."""

    get_resource = {
        'accepted': accepted,
        'rejected': rejected,
        'not_sure': unsure,
        'not_validated': unchecked,
        'mixed': mixed
    }

    get_triples = {
        'accepted': accepted_doc,
        'rejected': rejected_doc,
        'not_sure': unsure_doc,
        'not_validated': unchecked_doc,
        'mixed': mixed_doc
    }

    def terminology(self):

        return F"{header('LINK VALIDATION TERMINOLOGY')}" \
               F"{self.accepted_doc}" \
               F"{self.rejected_doc}" \
               F"{self.unsure_doc}" \
               F"{self.unchecked_doc}" \
               F"{self.mixed_doc}"

