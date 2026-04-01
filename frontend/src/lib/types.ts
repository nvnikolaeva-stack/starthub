export type SportType =
  | "swimming"
  | "triathlon"
  | "running"
  | "cycling"
  | "other";

export interface Registration {
  id: string;
  event_id: string;
  participant_id: string;
  participant?: Participant;
  distances: string[];
  result_time: string | null;
  result_place: string | null;
  created_at?: string;
  /** из EventDetail API */
  participant_display_name?: string;
  participant_telegram_username?: string | null;
}

export interface Participant {
  id: string;
  display_name: string;
  telegram_username: string | null;
  telegram_id?: number | null;
  normalized_name?: string;
  created_at?: string;
}

export interface SimilarEventMatch {
  id: string;
  name: string;
  date_start: string;
  location: string;
  sport_type: SportType | string;
  participants_count: number;
  participants: string[];
}

export interface SimilarEventsResponse {
  exact_matches: SimilarEventMatch[];
  date_matches: SimilarEventMatch[];
}

export interface Event {
  id: string;
  name: string;
  date_start: string;
  date_end: string | null;
  location: string;
  sport_type: SportType;
  url: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  registrations?: Registration[];
}

export interface CommunityStats {
  total_events: number;
  total_participants: number;
  most_active_participant: {
    participant_id?: string;
    display_name: string;
    registrations_count: number;
  } | null;
  popular_sports: { sport?: string; sport_type?: string; count: number }[];
  popular_locations: { location: string; count: number }[];
}

export interface ParticipantStats {
  total_events: number;
  events_by_sport: Record<string, number>;
  personal_records: Record<string, string>;
  places_history: Array<{
    event_name: string;
    date_start: string;
    result_place: string;
    sport_type: string;
  }>;
}

export interface ParticipantEventEntry {
  registration_id: string;
  event_id: string;
  event_name: string;
  date_start: string;
  sport_type: string;
  location: string;
  distances: string[];
  result_time: string | null;
  result_place: string | null;
}

export interface ParticipantDetail extends Participant {
  events: ParticipantEventEntry[];
}
