
from functools import reduce
from typing import List
import random
from itertools import combinations
from math import factorial, ceil

# SCRIPT OVERVIEW ###########################################################################################
#                                                                                                           #
#   THis class enable the interpretation of TRUTH VALUES in a non traditional manner                        #
#   by allowing logic computations of truth values in the interval [0, 1] based on a                        #
#   set of functions defined as T-norms (for conjunction) or T-conorms (for disjunction).                   #
#                                                                                                           #
# ###########################################################################################################


class LogicOperations:

    translation = {1: 'AND [Minimum t-norm (⊤min)]',
                   2: 'AND [Hamacher Product (⊤H0)]',
                   3: 'AND [Product t-norm (⊤prod)]',
                   4: 'AND [Nilpotent Minimum (⊤nM)]',
                   5: 'AND [Łukasiewicz t-norm (⊤Luk)]',
                   6: 'AND [Drastic t-norm (⊤D)]',

                   7: 'OR [Maximum s-norm (⊥max)]',
                   8: 'OR [Probabilistic Sum (⊥sum)]',
                   9: 'OR [Bounded Sum (⊥Luk)]',
                   10: 'OR [Drastic s-norm (⊥D)]',
                   11: 'OR [Nilpotent Maximum (⊥nM)]',
                   12: 'OR [Einstein Sum (⊥D)]'}

    operator_format = {

        'and': translation[1],
        'min': translation[1],
        'minimum': translation[1],
        'minimum_t_norm': translation[1],

        'hamacher': translation[2],
        'hamacher_product': translation[2],

        'prod': translation[3],
        'product': translation[3],
        'product_t_norm': translation[3],

        'nil min': translation[4],
        'nilpotent minimum': translation[4],
        'nilpotent_minimum': translation[4],

        'luk': translation[5],
        'lukasiewicz_t_norm': translation[5],

        'drastic t norm': translation[6],
        'drastic_t_norm': translation[6],

        # -------------------------------------------------------- #

        'or': translation[7],
        'max': translation[7],
        'maximum': translation[7],
        'maximum_t_conorm': translation[7],

        'prob': translation[8],
        "probabilistic": translation[8],
        "probabilistic_sum": translation[8],

        'bounded': translation[9],
        'bounded sum': translation[9],
        'bounded_sum': translation[9],

        'drastic t conorm': translation[10],
        'drastic_t_conorm': translation[10],

        'nilpotent max': 'Nilpotent Maximum (⊥nM)',
        'nil max': translation[11],
        'nilpotent maximum': translation[11],
        'nilpotent_maximum': translation[11],

        'einstein': translation[12],
        'einstein sum': translation[12],
        'einstein_sum': translation[12],
    }

    norms = {

        # Return the minimum of two values
        'minimum': lambda a, b: min(a, b),

        # Return 0 if both parameters are 0 otherwise, compute the product over the sum minus the product ab / (a + b - ab)
        'hamacher': lambda a, b: a * b / (a + b - (a * b) if (a == b == 0) is False else 0.0),

        # Retun the product of both values
        'product': lambda a, b: a * b,

        # Return the minimum of two values if their sum is greater than 1 otherwise return 0
        'nilpotent': lambda a, b: min(a, b) if a + b > 1 else 0.0,

        # Return the maximum between 0 and the sum minus 1
        'luk': lambda a, b: max(0.0, a + b - 1.0),

        # If one of the values is one, return the other value otherwise, return 0
        'drastic': lambda a, b: a if b == 1 else (b if a == 1 else 0.0)
    }

    conorms = {

        # If one of the values is 0, return the other value otherwise, return 1
        'drastic': lambda a, b: a if b == 0 else (b if a == 0 else 1.0),

        # Return the minimum between the sum of values and 1
        'bounded': lambda a, b: min(a + b, 1.0),

        # Return the sum of values over 1 plus the product of values
        'Einstein': lambda a, b: (a + b) / (1 + a * b),

        # Return the sum minus the product of the values
        'probabilistic': lambda a, b: a + b - (a * b),

        # Return the minimum if the sum is less than 1 otherwise 0
        'nilpotent': lambda a, b: max(a, b) if a + b < 1 else 1.0,

        # Return the maximum value
        'maximum': lambda a, b: max(a, b)
    }

    @staticmethod
    def tNorm(a: float, b: float, norm):
        # Using the function [get(key, default=None)] over a dictionary object enables the returns of a preset default
        # value if [key] is not in dictionary. As such, LogicOperations.norms.get(norm, lambda a, b: min(a, b)) returns
        # the appropriate T-norm function if the T-norm parameter is correctly provided. Otherwise, the default T-norm
        # [min(a, b)] function is returned.
        return round(LogicOperations.norms.get(norm.lower(), lambda x, y: min(x, y))(a, b), 5)

    @staticmethod
    def tConorm(a: float, b: float, conorm):
        # Using the function [get(key, default=None)] over a dictionary object enables the returns of a preset default
        # value if [key] is not in dictionary. As such, LogicOperations.norms.get(norm, lambda a, b: min(a, b)) returns
        # the appropriate T-norm function if the T-norm parameter is correctly provided. Otherwise, the default T-norm
        # [max(a, b)] function is returned.
        return round(LogicOperations.conorms.get(conorm.lower(), lambda x, y: max(x, y))(a, b))

    @staticmethod
    # Using the reduce function, the t_norm_list enables logical computation over a list of truth values based on a
    # single T_norm operator. for example using the HAMACHER (⊤H0) function over list of truth values [0.89, 0.82, 1]
    # wen obtain 0.74 while ⊤Luk and ⊤min respectively generate 0.71 and 0.82.
    def tNormList(truths: List[float], norm: str):
        return round(reduce(LogicOperations.norms.get(norm.lower(), lambda x, y: min(x, y)), truths), 5)

    @staticmethod
    # Like the t_norm_list function, the t_conorm_list function also applies to a list of truth values.
    def tConormList(truths: List[float], conorm: str):
        return round(reduce(LogicOperations.conorms.get(conorm.lower(), lambda x, y: max(x, y)), truths), 5)

    @staticmethod
    def listIntersectionStrength(strengths: List[float], intersection_threshold: float, norm: str = "min", conorm: str = 'max'):

        """
        :param strengths                    : THE MATCHED STRENGTHS
        :param intersection_threshold       : THE Intersection-threshold NUMBER, OTHERWISE THE CONVERSION OF PERCENTAGE
                                                TO NUMBER. THE LATTER IS BASED ON THE SMALLEST EVENT SIZE. IF THRESHOLD
                                                IS 50% AND WE MATCH A LIST OF 5 AGAINST 8, THEN minimum = ceil(5 * 0.5)
        :param norm                         : THE NAME OF THE T-NORM OPTION
        :param conorm                       : THE NAME OF THE CO-NORM OPTION
        :return                             : THE FINAL STRENGTH
        """

        intersection_threshold = ceil(intersection_threshold)
        n, k = len(strengths), intersection_threshold

        # GENERATE ALL POSSIBLE COMBINATIONS OF TUPLE OF SIZE MINIMUM
        possibilities = list(combinations(strengths, k))

        # (AND) COMPUTE THE T-NORM OF EACH COMBINATION
        options = [LogicOperations.tNormList(list(combination_option), norm) for combination_option in possibilities]

        # (OR) COMPUTE THE FINAL STRENGTH WHICH IS THE MAXIMUM OF THE PREVIOUS MINIMUMS
        strength = LogicOperations.tConormList(options, conorm)

        # # PRINT TO CHECK THE RESULT
        # print(F"""
        # DATA SIZE       : {n}
        # TUPLE SIZE      : {k}
        # COMBINATIONS    : {factorial(n) / (factorial(k) * factorial(n - k))}
        # DRASTIC MIN     : {min(strengths)}
        # optimum min     : {strength}
        # """)
        # print(
        #     LogicOperations.listIntersectionStrength(
        #         strengths=[0.89, 0.89, 0.82, 0.75, 0.89, 0.78],
        #         intersection_threshold=2))

        return strength

