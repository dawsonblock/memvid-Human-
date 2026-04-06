use serde::{Deserialize, Serialize};

/// High-level governed memory types.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MemoryType {
    Trace,
    Episode,
    Fact,
    Preference,
    GoalState,
}

/// Current status of an explicit belief.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BeliefStatus {
    Active,
    Disputed,
    Stale,
    Retracted,
}

/// Intent classes for governed retrieval.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum QueryIntent {
    CurrentFact,
    HistoricalFact,
    PreferenceLookup,
    TaskState,
    EpisodicRecall,
    SemanticBackground,
}

/// Trust source of a memory observation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceType {
    Chat,
    File,
    Tool,
    System,
    External,
}

/// Visibility / applicability scope.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Scope {
    Private,
    Task,
    Project,
    Shared,
}

/// Result of the promotion gate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PromotionDecision {
    Reject,
    StoreTrace,
    Promote,
}

/// Belief state transition kinds.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BeliefAction {
    Reinforce,
    Update,
    Dispute,
    Retract,
}
