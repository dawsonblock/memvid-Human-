use std::collections::BTreeMap;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use super::enums::{BeliefStatus, MemoryType, PromotionDecision, QueryIntent, Scope, SourceType};

/// Provenance metadata attached to a memory candidate.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Provenance {
    pub source_type: SourceType,
    pub source_id: String,
    pub source_label: Option<String>,
    pub observed_by: Option<String>,
    pub trust_weight: f32,
}

/// Memory candidate before promotion.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CandidateMemory {
    pub candidate_id: String,
    pub observed_at: DateTime<Utc>,
    pub entity: String,
    pub slot: String,
    pub value: String,
    pub raw_text: String,
    pub source: Provenance,
    pub memory_type: MemoryType,
    pub confidence: f32,
    pub salience: f32,
    pub scope: Scope,
    pub ttl: Option<i64>,
    pub event_at: Option<DateTime<Utc>>,
    pub valid_from: Option<DateTime<Utc>>,
    pub valid_to: Option<DateTime<Utc>>,
    pub tags: Vec<String>,
    pub metadata: BTreeMap<String, String>,
    pub is_retraction: bool,
}

/// Durable stored memory record.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DurableMemory {
    pub memory_id: String,
    pub candidate_id: String,
    pub stored_at: DateTime<Utc>,
    pub entity: String,
    pub slot: String,
    pub value: String,
    pub raw_text: String,
    pub memory_type: MemoryType,
    pub confidence: f32,
    pub salience: f32,
    pub scope: Scope,
    pub ttl: Option<i64>,
    pub source: Provenance,
    pub event_at: Option<DateTime<Utc>>,
    pub valid_from: Option<DateTime<Utc>>,
    pub valid_to: Option<DateTime<Utc>>,
    pub tags: Vec<String>,
    pub metadata: BTreeMap<String, String>,
    pub is_retraction: bool,
}

/// Explicit current belief state with supporting history references.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BeliefRecord {
    pub belief_id: String,
    pub entity: String,
    pub slot: String,
    pub current_value: String,
    pub status: BeliefStatus,
    pub confidence: f32,
    pub valid_from: DateTime<Utc>,
    pub valid_to: Option<DateTime<Utc>>,
    pub last_reviewed_at: DateTime<Utc>,
    pub supporting_memory_ids: Vec<String>,
    pub opposing_memory_ids: Vec<String>,
    pub source_weights: BTreeMap<SourceType, f32>,
}

/// Type-specific retention policy.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RetentionRule {
    pub memory_type: MemoryType,
    pub default_ttl: Option<i64>,
    pub decay_per_day: f32,
    pub retrieval_priority: f32,
    pub promotable: bool,
}

/// Retrieval request shaped by task intent.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RetrievalQuery {
    pub query_text: String,
    pub intent: QueryIntent,
    pub entity: Option<String>,
    pub slot: Option<String>,
    pub scope: Option<Scope>,
    pub top_k: usize,
    pub as_of: Option<DateTime<Utc>>,
    pub include_expired: bool,
}

/// Retrieval result emitted by the governed layer.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RetrievalHit {
    pub memory_id: Option<String>,
    pub belief_id: Option<String>,
    pub entity: Option<String>,
    pub slot: Option<String>,
    pub value: Option<String>,
    pub text: String,
    pub memory_type: Option<MemoryType>,
    pub score: f32,
    pub timestamp: DateTime<Utc>,
    pub scope: Option<Scope>,
    pub source: Option<SourceType>,
    pub from_belief: bool,
    pub expired: bool,
    pub metadata: BTreeMap<String, String>,
}

/// Promotion outcome for a candidate.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PromotionResult {
    pub decision: PromotionDecision,
    pub score: f32,
    pub reason: String,
    pub durable_memory: Option<DurableMemory>,
}

/// Append-only audit event.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AuditEvent {
    pub event_id: String,
    pub occurred_at: DateTime<Utc>,
    pub action: String,
    pub candidate_id: Option<String>,
    pub memory_id: Option<String>,
    pub belief_id: Option<String>,
    pub query_text: Option<String>,
    pub details: BTreeMap<String, String>,
}
