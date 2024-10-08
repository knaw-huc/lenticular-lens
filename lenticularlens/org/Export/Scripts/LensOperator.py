from lenticularlens.org.Export.Scripts.Resources import Resource as Rsc


labels = {
    'union': "Union",
    'difference': 'Difference',
    'sym_difference': 'Symmetric Difference',
    'intersection': 'Intersection',
    'in_set_and': 'In Set And',
    'in_set_or': 'In Set Or',
    'in_set_source': 'In Set Source',
    'in_set_target': 'In Set Target',
}

descriptions = {

    'union': """
        The Union is in the Lenticular Lens a set-like operator that unifies a collection of sets of links into a  
        single set of all links stemmed from the collection. 
        In such a unified set, when dealing with links using symmetric predicates such as identity predicates of the 
        likes of owl:sameAs, the duplication of links is not allowed. For example, <resource:1 owl:sameAs resource:2> 
        and <resource:2 owl:sameAs resource:1> are not both admitted in the resulting set. Only one of the two is 
        consistently permitted.""",

    'intersection': """
        The Intersection is in the Lenticular Lens a set-like operator between two sets A and B of links that results  
        in links that are in both sets A and B.
        In such a result-set, when dealing with links using symmetric predicates such as identity predicates of the 
        likes of owl:sameAs, the duplication of links is not allowed. For example, <resource:1 owl:sameAs resource:2> 
        and <resource:2 owl:sameAs resource:1> are not both admitted in the resulting set. Only one of the two is 
        consistently permitted.""",

    'difference': """
        The Difference is in the Lenticular Lens a set-like operator between two sets A and B of links that results in 
        links stemmed from A that are not in B.""",

    'sym_difference': """
        The Symmetric Difference is in the Lenticular Lens a set-like operator between two sets A and B of links that  
        results in links stemmed from A or B that are not in A and B.""",

    'in_set_and': """
        The In Set And is in the Lenticular Lens a set-like operator between two sets A (set of resources) and B (set of 
        links) that results in a subset of links from B where only resources from A occur as both the subject AND object 
        of each link.""",

    'in_set_or': """
        The In Set Or is in the Lenticular Lens a set-like operator between two sets A (set of resources) and B (set of 
        links) that results in a subset of links from B where only resources from A occur as the subject OR the object 
        of each link.""",

    'in_set_source': """
        The In Set Source is in the Lenticular Lens a set-like operator between two sets A (set of resources) and B (set 
        of links) that results in a subset of links from B where only resources from A occur as the subject of each link.""",

    'in_set_target': """
        The In Set Target is in the Lenticular Lens a set-like operator between two sets A (set of resources) and B (set  
        of links) that results in a subset of links from B where only resources from A occur as the target of each link."""
}


def resource(operator):
    return F"{Rsc.operator}{labels.get(operator.lower(), 'Unknown').replace(' ', '')}"


def resource_ttl(operator):
    return Rsc.operator_ttl(labels.get(operator.lower(), 'Unknown').replace(' ', ''))


def label(operator):
    return labels.get(operator.lower(), 'Unknown')


def description(operator):
    return descriptions.get(operator.lower(), 'Unknown')


