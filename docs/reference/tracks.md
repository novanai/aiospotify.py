::: spotify.api.API
    options:
      members:
        - get_track
        - get_several_tracks
        - get_users_saved_tracks
        - save_tracks_for_current_user
        - remove_users_saved_tracks
        - check_users_saved_tracks
::: spotify.models.SimpleTrack
    options:
      members:
        - artists
        - available_markets
        - disc_number
        - duration
        - explicit
        - external_urls
        - href
        - id
        - is_playable
        - linked_from
        - restrictions
        - name
        - preview_url
        - track_number
        - is_local
        - uri
::: spotify.models.Track
    options:
      members:
        - album
        - artists
        - available_markets
        - disc_number
        - duration
        - explicit
        - external_ids
        - external_urls
        - href
        - id
        - is_playable
        - linked_from
        - restrictions
        - name
        - popularity
        - preview_url
        - track_number
        - is_local
        - uri
::: spotify.models.TrackWithSimpleArtist
    options:
      members:
        - album
        - artists
        - available_markets
        - disc_number
        - duration
        - explicit
        - external_ids
        - external_urls
        - href
        - id
        - is_playable
        - linked_from
        - restrictions
        - name
        - popularity
        - preview_url
        - track_number
        - is_local
        - uri
::: spotify.models.LinkedFromTrack
::: spotify.models.SavedTrack
