from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Iterable, TypeVar, Protocol, runtime_checkable

Q = TypeVar("Q")
C = TypeVar("C")


@dataclass
class StageLog:
    stage: str
    detail: str


@dataclass
class PipelineResult(Generic[C]):
    candidates: list[C]
    logs: list[StageLog] = field(default_factory=list)


@runtime_checkable
class QueryHydrator(Protocol[Q]):
    def hydrate(self, query: Q) -> StageLog | None:
        ...


@runtime_checkable
class Source(Protocol[Q, C]):
    def fetch(self, query: Q) -> list[C]:
        ...


@runtime_checkable
class Hydrator(Protocol[Q, C]):
    def hydrate(self, query: Q, candidates: list[C]) -> StageLog | None:
        ...


@runtime_checkable
class Filter(Protocol[Q, C]):
    def filter(self, query: Q, candidates: list[C]) -> tuple[list[C], StageLog | None]:
        ...


@runtime_checkable
class Scorer(Protocol[Q, C]):
    def score(self, query: Q, candidates: list[C]) -> StageLog | None:
        ...


@runtime_checkable
class Selector(Protocol[Q, C]):
    def select(self, query: Q, candidates: list[C]) -> tuple[list[C], StageLog | None]:
        ...


@runtime_checkable
class SideEffect(Protocol[Q, C]):
    def run(self, query: Q, candidates: list[C]) -> StageLog | None:
        ...


@dataclass
class CandidatePipeline(Generic[Q, C]):
    query_hydrators: list[QueryHydrator[Q]]
    sources: list[Source[Q, C]]
    candidate_hydrators: list[Hydrator[Q, C]]
    filters: list[Filter[Q, C]]
    scorers: list[Scorer[Q, C]]
    selector: Selector[Q, C]
    post_filters: list[Filter[Q, C]]
    side_effects: list[SideEffect[Q, C]]

    def run(self, query: Q) -> PipelineResult[C]:
        logs: list[StageLog] = []

        for hydrator in self.query_hydrators:
            log = hydrator.hydrate(query)
            if log:
                logs.append(log)

        candidates: list[C] = []
        for source in self.sources:
            candidates.extend(source.fetch(query))
        logs.append(StageLog(stage="sources", detail=f"Retrieved {len(candidates)} candidates"))

        for hydrator in self.candidate_hydrators:
            log = hydrator.hydrate(query, candidates)
            if log:
                logs.append(log)

        for stage_filter in self.filters:
            candidates, log = stage_filter.filter(query, candidates)
            if log:
                logs.append(log)

        for scorer in self.scorers:
            log = scorer.score(query, candidates)
            if log:
                logs.append(log)

        candidates, log = self.selector.select(query, candidates)
        if log:
            logs.append(log)

        for post_filter in self.post_filters:
            candidates, log = post_filter.filter(query, candidates)
            if log:
                logs.append(log)

        for side_effect in self.side_effects:
            log = side_effect.run(query, candidates)
            if log:
                logs.append(log)

        return PipelineResult(candidates=candidates, logs=logs)
