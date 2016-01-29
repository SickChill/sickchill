#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Processor functions
"""
from logging import getLogger

from .utils import IdentitySet

from .rules import Rule, RemoveMatch

log = getLogger(__name__).log

DEFAULT = '__default__'

POST_PROCESS = -2048
PRE_PROCESS = 2048


def _default_conflict_solver(match, conflicting_match):
    """
    Default conflict solver for matches, shorter matches if they conflicts with longer ones

    :param conflicting_match:
    :type conflicting_match:
    :param match:
    :type match:
    :return:
    :rtype:
    """
    if len(conflicting_match.initiator) < len(match.initiator):
        return conflicting_match
    elif len(match.initiator) < len(conflicting_match.initiator):
        return match
    return None


class ConflictSolver(Rule):
    """
    Remove conflicting matches.
    """
    priority = PRE_PROCESS

    consequence = RemoveMatch

    @property
    def default_conflict_solver(self):  # pylint:disable=no-self-use
        """
        Default conflict solver to use.
        """
        return _default_conflict_solver

    def when(self, matches, context):
        to_remove_matches = IdentitySet()
        for match in filter(lambda match: not match.private, matches):
            conflicting_matches = matches.conflicting(match)

            if conflicting_matches:
                # keep the match only if it's the longest
                for conflicting_match in filter(lambda match: not match.private, conflicting_matches):
                    reverse = False
                    conflict_solvers = [(self.default_conflict_solver, False)]

                    if match.conflict_solver:
                        conflict_solvers.append((match.conflict_solver, False))
                    if conflicting_match.conflict_solver:
                        conflict_solvers.append((conflicting_match.conflict_solver, True))

                    for conflict_solver, reverse in reversed(conflict_solvers):
                        if reverse:
                            to_remove = conflict_solver(conflicting_match, match)
                        else:
                            to_remove = conflict_solver(match, conflicting_match)
                        if to_remove == DEFAULT:
                            continue
                        if to_remove and to_remove not in to_remove_matches:
                            to_remove_matches.add(to_remove)
                        break
        return to_remove_matches


class PrivateRemover(Rule):
    """
    Removes private matches rule.
    """
    priority = POST_PROCESS

    consequence = RemoveMatch

    def when(self, matches, context):
        return [match for match in matches if match.private]

