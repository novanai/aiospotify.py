from __future__ import annotations

import datetime
import typing

import pydantic

from spotify import enums, utils

__all__: typing.Sequence[str] = (
    "SavedAlbum",
    "SimpleAlbum",
    "ArtistAlbum",
    "Album",
    "SimpleArtist",
    "Artist",
    "SimpleAudiobook",
    "Audiobook",
    "Author",
    "AudioFeatures",
    "AudioAnalysis",
    "AudioAnalysisMeta",
    "AudioAnalysisTrack",
    "AudioAnalysisBar",
    "AudioAnalysisBeat",
    "AudioAnalysisSection",
    "AudioAnalysisSegment",
    "AudioAnalysisTatum",
    "Category",
    "SimpleChapter",
    "Chapter",
    "Copyright",
    "SavedEpisode",
    "SimpleEpisode",
    "Episode",
    "ExplicitContent",
    "ExternalIDs",
    "ExternalURLs",
    "Followers",
    "Image",
    "Narrator",
    "PlayerTrack",
    "Player",
    "Device",
    "Context",
    "Actions",
    "PlayHistory",
    "Queue",
    "SimplePlaylist",
    "Playlist",
    "PlaylistTracks",
    "PlaylistItem",
    "Playlists",
    "BasePaginator",
    "Paginator",
    "CursorPaginator",
    "Cursors",
    "Restrictions",
    "ResumePoint",
    "SavedShow",
    "SimpleShow",
    "Show",
    "SearchResult",
    "SavedTrack",
    "LinkedFromTrack",
    "SimpleTrack",
    "Track",
    "TrackWithSimpleArtist",
    "SimpleUser",
    "User",
    "OwnUser",
    "Recommendations",
    "RecommendationSeed",
)


ArtistT = typing.TypeVar("ArtistT", bound="SimpleArtist")
T = typing.TypeVar("T")


class BaseModel(pydantic.BaseModel):
    # Occasionally, this value for this field is upper case, so we convert it to lower case
    @pydantic.field_validator("album_type", mode="before", check_fields=False)
    @classmethod
    def album_type_validator(cls, v: str):
        return v.lower()

    @pydantic.field_validator("release_date", mode="before", check_fields=False)
    @classmethod
    def release_date_validator(cls, v: str | None) -> datetime.datetime | None:
        if v == "0000" or v is None:
            return None

        return utils.datetime_from_timestamp(v)


class DurationMS(pydantic.BaseModel):
    @pydantic.field_validator("duration", mode="before", check_fields=False)
    @classmethod
    def duration_validator(cls, v: int) -> float:
        return v / 1000


class SavedAlbum(BaseModel):
    """Information about an album saved to a user's 'Your Music' library."""

    added_at: datetime.datetime
    """The date and time the album was saved."""
    album: Album
    """The album."""


class SimpleAlbum(BaseModel):
    """A simplified album."""

    album_type: enums.AlbumType
    """The type of the album."""
    total_tracks: int
    """The number of tracks in the album."""
    available_markets: list[str] | None = None
    """The markets in which the album is available
    ([ISO 3166-1 alpha-2 country codes](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)).
    
    !!! note
        An album is considered available in a market when at least 1 of its tracks is available in
        that market.
    """
    external_urls: ExternalURLs
    """Known external URLs for the album."""
    href: str
    """A link to the Web API endpoint providing full details of the album."""
    id: str
    """The Spotify ID for the album."""
    images: list[Image]
    """The cover art for the album in various sizes, widest first."""
    name: str
    """The name of the album.

    !!! note
        In case of an album takedown, the value may be an empty string.
    """
    release_date: datetime.date
    """The date the album was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which [`release_date`][spotify.models.SimpleAlbum.release_date] is
    known.
    """
    restrictions: Restrictions | None = None
    """Restrictions applied to the album. Included when a content restriction is applied."""
    uri: str
    """The Spotify URI for the album."""
    artists: list[SimpleArtist]
    """The artists of the album."""


class ArtistAlbum(SimpleAlbum):
    """An artist's album."""

    album_group: enums.AlbumGroup
    """Represents the relationship between the artist and the album."""


class Album(SimpleAlbum):
    """An album."""

    tracks: Paginator[SimpleTrack]
    """The tracks of the album."""
    copyrights: list[Copyright]
    """The copyright statements of the album."""
    external_ids: ExternalIDs
    """Known external IDs for the album."""
    genres: list[str]
    """The genres the album is associated with. If not yet classified, this list is empty."""
    label: str
    """The label associated with the album."""
    popularity: int
    """The popularity of the album. The value will be between 0 and 100, with 100 being the most
    popular.
    """


class SimpleArtist(BaseModel):
    """A simplified artist."""

    external_urls: ExternalURLs
    """Known external URLs for the artist."""
    href: str
    """A link to the Web API endpoint providing full details of the artist."""
    id: str
    """The Spotify ID for the artist."""
    name: str
    """The name of the artist."""
    uri: str
    """The Spotify URI for the artist."""


class Artist(SimpleArtist):
    """An artist."""

    followers: Followers
    """Information about the followers of the artist."""
    genres: list[str]
    """A list of the genres the artist is associated with. If not yet classified, the list is
    empty.
    """
    images: list[Image]
    """Images of the artist in various sizes, widest first."""
    popularity: int
    """The popularity of the artist. The value will be between 0 and 100, with 100 being the most
    popular. The artist's popularity is calculated from the popularity of all the artist's tracks.
    """


class SimpleAudiobook(BaseModel):
    """A simplified audiobook."""

    authors: list[Author]
    """The author(s) of the audiobook."""
    available_markets: list[str]
    """A list of the countries in which the audiobook can be played, identified by their
    [ISO 3166-1 alpha-2 code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
    """
    copyrights: list[Copyright]
    """The copyright statements of the audiobook."""
    description: str
    """A description of the audiobook. HTML tags are stripped away from this field, use the
    [`html_description`][spotify.models.SimpleAudiobook.html_description] field in case HTML tags
    are needed.
    """
    html_description: str
    """A description of the audiobook. This field may contain HTML tags."""
    edition: str | None
    """The edition of the audiobook."""
    explicit: bool
    """Whether or not the audiobook has explicit content."""
    external_urls: ExternalURLs
    """External URLs for the audiobook."""
    href: str
    """A link to the Web API endpoint providing full details of the audiobook."""
    id: str
    """The Spotify ID for the audiobook."""
    images: list[Image]
    """The cover art for the audiobook in various sizes, widest first."""
    languages: list[str]
    """A list of the languages used in the audiobook, identified by their
    [ISO 639 code](https://en.wikipedia.org/wiki/ISO_639).
    """
    media_type: str
    """The media type of the audiobook."""
    name: str
    """The name of the audiobook."""
    narrators: list[Narrator]
    """The narrator(s) of the audiobook."""
    publisher: str
    """The publisher of the audiobook."""
    uri: str
    """The Spotify URI for the audiobook."""
    total_chapters: int | None
    """The number of chapters in the audiobook."""


class Audiobook(SimpleAudiobook):
    """An audiobook."""

    chapters: Paginator[SimpleChapter]
    """The chapters of the audiobook."""


class Author(BaseModel):
    """Audiobook author information."""

    name: str
    """The name of the author."""


class AudioFeatures(BaseModel, DurationMS):
    """Track audio features."""

    acousticness: float
    """A confidence measure from `0.0` to `1.0` of whether the track is acoustic. `1.0` represents
    high confidence the track is acoustic.
    """
    analysis_url: str
    """A link to the Web API endpoint providing full details of the audio analysis."""
    danceability: float
    """Danceability describes how suitable a track is for dancing based on a combination of
    musical elements including tempo, rhythm stability, beat strength, and overall regularity.
    A value of `0.0` is least danceable and `1.0` is most danceable.
    """
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
    """The duration of the track."""
    energy: float
    """Energy is a measure from `0.0` to `1.0` and represents a perceptual measure of intensity
    and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal
    has high energy, while a Bach prelude scores low on the scale. Perceptual features
    contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate,
    and general entropy.
    """
    id: str
    """The Spotify ID for the track."""
    instrumentalness: float
    """Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as
    instrumental in this context. Rap or spoken word tracks are clearly "vocal". The closer the
    instrumentalness value is to `1.0`, the greater likelihood the track contains no vocal
    content. Values above `0.5` are intended to represent instrumental tracks, but confidence is
    higher as the value approaches `1.0`.
    """
    # TODO: maybe use an enum for this value?
    key: int
    """The key the track is in. Integers map to pitches using standard
    [Pitch Class notation](https://en.wikipedia.org/wiki/Pitch_class). E.g. `0` = C, `1` = C♯/D♭,
    `2` = D, and so on. If no key was detected, the value is `-1`.
    """
    liveness: float
    """Detects the presence of an audience in the recording. Higher liveness values represent an
    increased probability that the track was performed live. A value above `0.8` provides strong
    likelihood that the track is live.
    """
    loudness: float
    """The overall loudness of a track in decibels (dB). Loudness values are averaged across the
    entire track and are useful for comparing relative loudness of tracks. Loudness is the quality
    of a sound that is the primary psychological correlate of physical strength (amplitude).
    Values typically range between `-60` and `0` dB.
    """
    mode: enums.TrackMode
    """Mode indicates the modality (major or minor) of a track, the type of scale from which its
    melodic content is derived.
    """
    speechiness: float
    """Speechiness detects the presence of spoken words in a track. The more exclusively
    speech-like the recording (e.g. talk show, audio book, poetry), the closer to `1.0` the
    attribute value. Values above `0.66` describe tracks that are probably made entirely of spoken
    words. Values between `0.33` and `0.66` describe tracks that may contain both music and
    speech, either in sections or layered, including such cases as rap music. Values below `0.33`
    most likely represent music and other non-speech-like tracks.
    """
    tempo: float
    """The overall estimated tempo of a track in beats per minute (BPM). In musical terminology,
    tempo is the speed or pace of a given piece and derives directly from the average beat
    duration.
    """
    time_signature: int
    """An estimated time signature. The time signature (meter) is a notational convention to
    specify how many beats are in each bar (or measure). The time signature ranges from `3` to `7`
    indicating time signatures of "3/4" to "7/4".
    """
    track_href: str
    """A link to the Web API endpoint providing full details of the track."""
    uri: str
    """The Spotify URI for the track."""
    valence: float
    """A measure from `0.0` to `1.0` describing the musical positiveness conveyed by a track.
    Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks
    with low valence sound more negative (e.g. sad, depressed, angry).
    """


class AudioAnalysis(BaseModel):
    """Track audio analysis."""

    meta: AudioAnalysisMeta
    """Metadata for the analysis."""
    track: AudioAnalysisTrack
    """Track information"""
    bars: list[AudioAnalysisBar]
    """The time intervals of the bars throughout the track."""
    beats: list[AudioAnalysisBeat]
    """The time intervals of beats throughout the track."""
    sections: list[AudioAnalysisSection]
    """Sections are defined by large variations in rhythm or timbre, e.g. chorus, verse, bridge,
    guitar solo, etc. Each section contains its own descriptions of
    [`tempo`][spotify.models.AudioAnalysisSection.tempo],
    [`key`][spotify.models.AudioAnalysisSection.key],
    [`mode`][spotify.models.AudioAnalysisSection.mode],
    [`time_signature`][spotify.models.AudioAnalysisSection.time_signature], and
    [`loudness`][spotify.models.AudioAnalysisSection.loudness].
    """
    segments: list[AudioAnalysisSegment]
    """Each segment contains a roughly consistent sound throughout its duration."""
    tatums: list[AudioAnalysisTatum]
    """A tatum represents the lowest regular pulse train that a listener intuitively infers from
    the timing of perceived musical events (segments).
    """


class AudioAnalysisMeta(BaseModel):
    """Audio analysis metadata."""

    analyzer_version: str
    """The version of the Analyzer used to analyze the track."""
    platform: str
    """The platform used to read the track's audio data."""
    detailed_status: str
    """A detailed status code for the track. If analysis data is missing, this code may explain
    why.
    """
    status_code: enums.StatusCode
    """The return code of the analyzer process."""
    timestamp: datetime.datetime
    """The time at which the track was analyzed."""
    analysis_time: datetime.timedelta
    """The amount of time taken to analyze the track."""
    input_process: str
    """The method used to read the track's audio data."""


class AudioAnalysisTrack(BaseModel):
    """Audio analysis track information."""

    num_samples: int
    """The exact number of audio samples analyzed from the track. See also
    [`analysis_sample_rate`][spotify.models.AudioAnalysisTrack.analysis_sample_rate].
    """
    duration: float
    """Length of the track in seconds."""
    sample_md5: str
    """This field will always contain an empty string."""
    offset_seconds: int
    """An offset to the start of the region of the track that was analyzed. (As the entire track
    is analyzed, this should always be `0`.)
    """
    window_seconds: int
    """The length of the region of the track was analyzed, if a subset of the track was analyzed.
    (As the entire track is analyzed, this should always be `0`.)
    """
    analysis_sample_rate: int
    """The sample rate used to decode and analyze the track. May differ from the actual sample
    rate of the track available on Spotify.
    """
    analysis_channels: int
    """The number of channels used for analysis. If `1`, all channels are summed together to mono
    before analysis.
    """
    end_of_fade_in: float
    """The time, in seconds, at which the track's fade-in period ends. If the track has no
    fade-in, this will be `0.0`.
    """
    start_of_fade_out: float
    """The time, in seconds, at which the track's fade-out period starts. If the track has no
    fade-out, this should match the track's length.
    """
    loudness: float
    """The overall loudness of a track in decibels (dB). Loudness values are averaged across the
    entire track and are useful for comparing relative loudness of tracks. Loudness is the quality
    of a sound that is the primary psychological correlate of physical strength (amplitude).
    Values typically range between `-60` and `0` dB.
    """
    tempo: float
    """The overall estimated tempo of a track in beats per minute (BPM). In musical terminology,
    tempo is the speed or pace of a given piece and derives directly from the average beat
    duration.
    """
    tempo_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`tempo`][spotify.models.AudioAnalysisTrack.tempo].
    """
    time_signature: int
    """An estimated time signature. The time signature (meter) is a notational convention to
    specify how many beats are in each bar (or measure). The time signature ranges from `3` to `7`
    indicating time signatures of "3/4" to "7/4".
    """
    time_signature_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`time_signature`][spotify.models.AudioAnalysisTrack.time_signature].
    """
    key: int
    """The key the track is in. Integers map to pitches using standard
    [Pitch Class notation](https://en.wikipedia.org/wiki/Pitch_class). E.g. `0` = C, `1` = C♯/D♭,
    `2` = D, and so on. If no key was detected, the value is `-1`.
    """
    key_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`key`][spotify.models.AudioAnalysisTrack.key].
    """
    mode: enums.TrackMode
    """Mode indicates the modality (major or minor) of a track, the type of scale from which its
    melodic content is derived.
    """
    mode_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`mode`][spotify.models.AudioAnalysisTrack.mode].
    """
    codestring: str
    """An [Echo Nest Musical Fingerprint (ENMFP)](https://academiccommons.columbia.edu/doi/10.7916/D8Q248M4)
    codestring for the track.
    """
    code_version: float
    """A version number for the Echo Nest Musical Fingerprint format used in the
    [`codestring`][spotify.models.AudioAnalysisTrack.codestring] field.
    """
    echoprintstring: str
    """An [EchoPrint](https://github.com/spotify/echoprint-codegen) codestring for the track."""
    echoprint_version: float
    """A version number for the EchoPrint format used in the
    [`echoprintstring`][spotify.models.AudioAnalysisTrack.echoprintstring] field.
    """
    synchstring: str
    """A [Synchstring](https://github.com/echonest/synchdata) for the track."""
    synch_version: float
    """A version number for the Synchstring used in the
    [`synchstring`][spotify.models.AudioAnalysisTrack.synchstring] field.
    """
    rhythmstring: str
    """A Rhythmstring for the track. The format of this string is similar to the Synchstring."""
    rhythm_version: float
    """A version number for the Rhythmstring used in the
    [`rhythmstring`][spotify.models.AudioAnalysisTrack.rhythmstring] field.
    """


class AudioAnalysisBar(BaseModel):
    """Audio analysis of a bar. A bar (or measure) is a segment of time defined as a given number
    of beats.
    """

    start: datetime.timedelta
    """The starting point of the time interval."""
    duration: datetime.timedelta
    """The duration of the time interval."""
    confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the interval."""


class AudioAnalysisBeat(BaseModel):
    """Audio analysis of a beat. A beat is the basic time unit of a piece of music; for example,
    each tick of a metronome. Beats are typically multiples of tatums.
    """

    start: datetime.timedelta
    """The starting point of the time interval."""
    duration: datetime.timedelta
    """The duration of the time interval."""
    confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the interval."""


class AudioAnalysisSection(BaseModel):
    """Audio analysis of a section. Sections are defined by large variations in rhythm or timbre,
    e.g. chorus, verse, bridge, guitar solo, etc. Each section contains its own descriptions of
    [`tempo`][spotify.models.AudioAnalysisSection.tempo],
    [`key`][spotify.models.AudioAnalysisSection.key],
    [`mode`][spotify.models.AudioAnalysisSection.mode],
    [`time_signature`][spotify.models.AudioAnalysisSection.time_signature], and
    [`loudness`][spotify.models.AudioAnalysisSection.loudness].
    """

    start: datetime.timedelta
    """The starting point of the section."""
    duration: datetime.timedelta
    """The duration of the section."""
    confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the section's "designation"."""
    loudness: float
    """The overall loudness of the section in decibels (dB). Loudness values are useful for
    comparing relative loudness of sections within tracks.
    """
    tempo: float
    """The overall estimated tempo of the section in beats per minute (BPM). In musical
    terminology, tempo is the speed or pace of a given piece and derives directly from the average
    beat duration.
    """
    tempo_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`tempo`][spotify.models.AudioAnalysisSection.tempo]. Some tracks contain tempo changes or
    sounds which don't contain tempo (like pure speech) which would correspond to a low value in
    this field.
    """
    key: int
    """The estimated overall key of the section. The values in this field ranging from `0` to `11`
    mapping to pitches using standard Pitch Class notation (E.g. `0` = C, `1` = C♯/D♭, `2` = D,
    and so on). If no key was detected, the value is `-1`.
    """
    key_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`key`][spotify.models.AudioAnalysisSection.key]. Songs with many key changes may correspond
    to low values in this field.
    """
    mode: enums.TrackMode
    """Indicates the modality (major or minor) of a section, the type of scale from which its
    melodic content is derived. Note that the major key (e.g. C major) could more likely be
    confused with the minor key at 3 semitones lower (e.g. A minor) as both keys carry the same
    pitches.
    """
    mode_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`mode`][spotify.models.AudioAnalysisSection.mode].
    """
    time_signature: int
    """An estimated time signature. The time signature (meter) is a notational convention to
    specify how many beats are in each bar (or measure). The time signature ranges from `3` to `7`
    indicating time signatures of "3/4" to "7/4".
    """
    time_signature_confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the
    [`time_signature`][spotify.models.AudioAnalysisSection.time_signature]. Sections with time
    signature changes may correspond to low values in this field.
    """


class AudioAnalysisSegment(BaseModel):
    """Audio analysis segment."""

    start: datetime.timedelta
    """The starting point of the segment."""
    duration: datetime.timedelta
    """The duration of the segment."""
    confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the segmentation. Segments of
    the song which are difficult to logically segment (e.g: noise) may correspond to low values in
    this field.
    """
    loudness_start: float
    """The onset loudness of the segment in decibels (dB). Combined with
    [`loudness_max`][spotify.models.AudioAnalysisSegment.loudness_max] and
    [`loudness_max_time`][spotify.models.AudioAnalysisSegment.loudness_max_time], these components
    can be used to describe the "attack" of the segment.
    """
    loudness_max: float
    """The peak loudness of the segment in decibels (dB). Combined with
    [`loudness_start`][spotify.models.AudioAnalysisSegment.loudness_start] and
    [`loudness_max_time`][spotify.models.AudioAnalysisSegment.loudness_max_time], these components
    can be used to describe the "attack" of the segment.
    """
    loudness_max_time: float
    """The segment-relative offset of the segment peak loudness in seconds. Combined with 
    [`loudness_start`][spotify.models.AudioAnalysisSegment.loudness_start] and
    [`loudness_max`][spotify.models.AudioAnalysisSegment.loudness_max], these components can be
    used to describe the "attack" of the
    segment.
    """
    loudness_end: float
    """The offset loudness of the segment in decibels (dB). This value should be equivalent to the
    [`loudness_start`][spotify.models.AudioAnalysisSegment.loudness_start] of the following
    segment.
    """
    pitches: list[float]
    """Pitch content is given by a "chroma" vector, corresponding to the 12 pitch classes C, C♯, D
    to B, with values ranging from `0` to `1` that describe the relative dominance of every pitch
    in the chromatic scale. For example a C Major chord would likely be represented by large
    values of C, E and G (i.e. classes `0`, `4`, and `7`).

    Vectors are normalized to `1` by their strongest dimension, therefore noisy sounds are likely
    represented by values that are all close to `1`, while pure tones are described by one value at
    `1` (the pitch) and others near `0`. As can be seen below, the 12 vector indices are a
    combination of low-power spectrum values at their respective pitch frequencies.

    ![](https://developer.spotify.com/assets/audio/Pitch_vector.png)
    Image source: [Spotify](https://developer.spotify.com/assets/audio/Pitch_vector.png)
    """
    timbre: list[float]
    """Timbre is the quality of a musical note or sound that distinguishes different types of
    musical instruments, or voices. It is a complex notion also referred to as sound color,
    texture, or tone quality, and is derived from the shape of a segment's spectro-temporal
    surface, independently of pitch and loudness. The timbre feature is a vector that includes 12
    unbounded values roughly centered around `0`. Those values are high level abstractions of the
    spectral surface, ordered by degree of importance.

    For completeness however, the first dimension represents the average loudness of the segment;
    second emphasizes brightness; third is more closely correlated to the flatness of a sound;
    fourth to sounds with a stronger attack; etc. See an image below representing the 12 basis
    functions (i.e. template segments).

    ![](https://developer.spotify.com/assets/audio/Timbre_basis_functions.png)
    Image source: [Spotify](https://developer.spotify.com/assets/audio/Timbre_basis_functions.png)
    
    The actual timbre of the segment is best described as a linear combination of these 12 basis
    functions weighted by the coefficient values: timbre = $c1 \\times b1 + c2 \\times b2 +
    \\ldots + c12 \\times b12$, where $c1$ to $c12$ represent the 12 coefficients and $b1$ to
    $b12$ the 12 basis functions as displayed below. Timbre vectors are best used in comparison
    with each other.
    """


class AudioAnalysisTatum(BaseModel):
    """Audio analysis tatum. A tatum represents the lowest regular pulse train that a listener
    intuitively infers from the timing of perceived musical events (segments).
    """

    start: datetime.timedelta
    """The starting point of the time interval."""
    duration: datetime.timedelta
    """The duration of the time interval."""
    confidence: float
    """The confidence, from `0.0` to `1.0`, of the reliability of the interval."""


class Category(BaseModel):
    """A category."""

    href: str
    """A link to the Web API endpoint returning full details of the category."""
    icons: list[Image]
    """The category icon, in various sizes."""
    id: str
    """The Spotify category ID of the category."""
    name: str
    """The name of the category."""


class SimpleChapter(BaseModel, DurationMS):
    """A simplified chapter."""

    audio_preview_url: str | None
    """A URL to a 30 second preview (MP3 format) of the chapter. [`None`][] if not available."""
    available_markets: list[str] | None
    """A list of the countries in which the chapter can be played, identified by their
    [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.
    """
    chapter_number: int
    """The number of the chapter."""
    description: str
    """A description of the chapter. HTML tags are stripped away from this field, use the
    [`html_description`][spotify.models.SimpleChapter.html_description] field in case HTML tags
    are needed.
    """
    html_description: str
    """A description of the chapter. This field may contain HTML tags."""
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
    """The chapter length."""
    explicit: bool
    """Whether or not the chapter has explicit content."""
    external_urls: ExternalURLs
    """External URLs for the chapter."""
    href: str
    """A link to the Web API endpoint providing full details of the chapter."""
    id: str
    """The Spotify ID for the chapter."""
    images: list[Image]
    """The cover art for the chapter in various sizes, widest first."""
    is_playable: bool | None = None
    """[`True`][] if the chapter is playable in the given market. Otherwise [`False`][]."""
    languages: list[str]
    """A list of the languages used in the chapter, identified by their
    [ISO 639-1 code](https://en.wikipedia.org/wiki/ISO_639).
    """
    name: str
    """The name of the chapter."""
    release_date: datetime.date | None
    """The date the chapter was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which [`release_date`][spotify.models.SimpleChapter.release_date] value
    is known.
    """
    resume_point: ResumePoint | None
    """The user's most recent position in the chapter.
    
    !!! scopes "Required Authorization Scope"
        [`USER_READ_PLAYBACK_POSITION`][spotify.enums.Scope.USER_READ_PLAYBACK_POSITION].
    """
    uri: str
    """The Spotify URI for the chapter."""
    restrictions: Restrictions | None = None
    """Present when a content restriction is applied."""


class Chapter(SimpleChapter):
    """A chapter."""

    audiobook: SimpleAudiobook
    """The audiobook on which the chapter appears."""


class Copyright(BaseModel):
    """Copyright statements."""

    text: str
    """The copyright text for the content."""
    type: enums.CopyrightType
    """The type of copyright."""


class SavedEpisode(BaseModel):
    """Information about an episode saved to a user's 'Your Music' library."""

    added_at: datetime.datetime
    """The date and time the episode was saved."""
    episode: Episode
    """The episode."""


class SimpleEpisode(BaseModel, DurationMS):
    """A simplified episode."""

    audio_preview_url: str | None
    """A URL to a 30 second preview (MP3 format) of the episode. [`None`][] if not available."""
    description: str
    """A description of the episode. HTML tags are stripped away from this field, use the
    [`html_description`][spotify.models.SimpleEpisode.html_description] field in case HTML tags
    are needed.
    """
    html_description: str
    """A description of the episode. This field may contain HTML tags."""
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
    """The episode length."""
    explicit: bool
    """Whether or not the episode has explicit content."""
    external_urls: ExternalURLs
    """External URLs for this episode."""
    href: str
    """A link to the Web API endpoint providing full details of the episode."""
    id: str
    """The Spotify ID for the episode."""
    images: list[Image]
    """The cover art for the episode in various sizes, widest first."""
    is_externally_hosted: bool
    """[`True`][] if the episode is hosted outside of Spotify's CDN. Otherwise [`False`][]."""
    is_playable: bool | None = None
    """[`True`][] if the episode is playable in the given market. Otherwise [`False`][]. May be 
    [`None`][] in some situations.
    """
    languages: list[str]
    """A list of the languages used in the episode, identified by their
    [ISO 639-1 code](https://en.wikipedia.org/wiki/ISO_639).
    """
    name: str
    """The name of the episode."""
    release_date: datetime.date
    """The date the episode was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which [`release_date`][spotify.models.SimpleEpisode.release_date] value 
    is known.
    """
    resume_point: ResumePoint | None = None
    """The user's most recent position in the episode.

    !!! scopes "Required Authorization Scope"
        [`USER_READ_PLAYBACK_POSITION`][spotify.enums.Scope.USER_READ_PLAYBACK_POSITION]
    """
    uri: str
    """The Spotify URI for the episode."""
    restrictions: Restrictions | None = None
    """Present when a content restriction is applied."""


class Episode(SimpleEpisode):
    """An episode."""

    show: SimpleShow
    """The show on which the episode appears."""


class ExplicitContent(BaseModel):
    """Explicit content settings."""

    filter_enabled: bool
    """When [`True`][], indicates that explicit content should not be played."""
    filter_locked: bool
    """When [`True`][], indicates that the explicit content setting is locked and can't be changed
    by the user.
    """


class ExternalIDs(BaseModel):
    """External IDs."""

    isrc: str | None = None
    """[International Standard Recording Code](http://en.wikipedia.org/wiki/International_Standard_Recording_Code)."""
    ean: str | None = None
    """[International Article Number](https://en.wikipedia.org/wiki/International_Article_Number_%28EAN%29)."""
    upc: str | None = None
    """[Universal Product Code](http://en.wikipedia.org/wiki/Universal_Product_Code)."""


class ExternalURLs(BaseModel):
    """External URLs."""

    spotify: str | None
    """The Spotify URL for the object."""


class Followers(BaseModel):
    """Information about followers."""

    href: str | None
    """This will always be set to [`None`][], as the Spotify Web API does not support it at the moment."""
    total: int
    """The total number of followers."""


class Image(BaseModel):
    """An image."""

    url: str
    """The source URL of the image."""
    height: int | None
    """The image height in pixels."""
    width: int | None
    """The image width in pixels."""


class Narrator(BaseModel):
    """Narrator information."""

    name: str
    """The name of the narrator."""


class PlayerTrack(BaseModel):
    """Information about the user's currently playing item."""

    context: Context | None
    """Limited information about the currently playing item."""
    timestamp: datetime.datetime
    """Time when playback state was last changed (play, pause, skip, scrub, new song, etc.)."""
    progress: datetime.timedelta | None = pydantic.Field(alias="progress_ms")
    """Progress into the currently playing track or episode."""
    is_playing: bool
    """[`True`][] if something is currently playing."""
    item: TrackWithSimpleArtist | Episode | None
    """The currently playing track or episode."""
    currently_playing_type: enums.PlayingType
    """The type of the currently playing item."""
    actions: Actions
    """Actions available to control playback."""

    @pydantic.field_validator("currently_playing_type", mode="before", check_fields=False)
    @classmethod
    def currently_playing_type_validator(cls, v: str) -> str:
        return v if v in ("track", "episode", "ad") else "unknown"

    @pydantic.field_validator("progress", mode="before", check_fields=False)
    @classmethod
    def progress_validator(cls, v: int) -> float:
        return v / 1000


class Player(PlayerTrack):
    """Information about the user's current playback state."""

    device: Device
    """The device that is currently active."""
    repeat_state: enums.RepeatState
    """Whether or not a repeat is applied to the playback state."""
    shuffle_state: bool
    """Whether or not shuffle is applied to the playback state."""


class Device(BaseModel):
    """Information about a playback device."""

    id: str | None
    """The device ID. This ID is unique and persistent to some extent. However, this is not 
    guaranteed and any cached device [`id`][spotify.models.Device.id] should periodically be
    cleared out and re-fetched as necessary.
    """
    is_active: bool
    """If this device is the currently active device."""
    is_private_session: bool
    """If this device is currently in a private session."""
    is_restricted: bool
    """Whether controlling this device is restricted. At present if this is [`True`][] then no Web
    API commands will be accepted by this device.
    """
    name: str
    """A human-readable name for the device. Some devices have a name that the user can configure
    (e.g. "Loudest speaker") and some devices have a generic name associated with the manufacturer
    or device model.
    """
    type: str
    """Device type, such as "computer", "smartphone" or "speaker".
    
    !!! note
        I did not add an enum for this field as there no official list of values.
        [This](https://github.com/spotify/web-api/issues/687#issuecomment-358783650) list from
        2018 exists, but I don't trust that it is up to date and contains all available devices.
    """
    volume_percent: int | None
    """The current volume in percent."""
    supports_volume: bool
    """If this device can be used to set the volume."""


class Context(BaseModel):
    """Limited information about the currently playing item."""

    type: enums.ContextType
    """The item type."""
    href: str
    """A link to the Web API endpoint providing full details of the item."""
    external_urls: ExternalURLs
    """External URLs for this context."""
    uri: str
    """The Spotify URI for the context."""


class Actions(BaseModel):
    """Actions available to control playback."""

    interrupting_playback: bool | None = None
    """Interrupting playback."""
    pausing: bool | None = None
    """Pausing."""
    resuming: bool | None = None
    """Resuming."""
    seeking: bool | None = None
    """Seeking playback position."""
    skipping_next: bool | None = None
    """Skipping to the next context."""
    skipping_prev: bool | None = None
    """Skipping to the previous context."""
    toggling_repeat_context: bool | None = None
    """Toggling repeat context flag."""
    toggling_shuffle: bool | None = None
    """Toggling shuffle flag."""
    toggling_repeat_track: bool | None = None
    """Toggling repeat track flag."""
    transferring_playback: bool | None = None
    """Transferring playback between devices."""


class PlayHistory(BaseModel):
    """Information about a track on a user's play history."""

    track: TrackWithSimpleArtist
    """The track the user listened to."""
    played_at: datetime.datetime
    """The date and time the track was played."""
    context: Context
    """The context the track was played from."""


class Queue(BaseModel):
    """Information about a user's queue."""

    currently_playing: Track | Episode | None
    """The currently playing track or episode."""
    queue: list[Track | Episode]
    """The tracks or episodes in the queue."""


class SimplePlaylist(BaseModel):
    """A simplified playlist."""

    collaborative: bool
    """[`True`][] if the owner allows other users to modify the playlist."""
    description: str | None
    """The playlist description. Only returned for modified, verified playlists, otherwise [`None`][]."""
    external_urls: ExternalURLs
    """Known external URLs for the playlist."""
    href: str
    """A link to the Web API endpoint providing full details of the playlist."""
    id: str
    """The Spotify ID for the playlist."""
    images: list[Image]
    """Images for the playlist."""
    name: str
    """The name of the playlist."""
    owner: User
    """The user who owns the playlist."""
    public: bool | None
    """The playlist's public/private status.

    * [`True`][] if the playlist is public.
    * [`False`][] if the playlist is private.
    * [`None`][] if the playlist status is not relevant.
    """
    snapshot_id: str
    """The version identifier for the current playlist. Can be supplied in other requests to
    target a specific playlist version.
    """
    tracks: PlaylistTracks
    """Link to the playlist's tracks."""
    uri: str
    """The Spotify URI for the playlist."""


class Playlist(SimplePlaylist):
    """A playlist."""

    followers: Followers
    """Information about the followers of the playlist."""
    tracks: Paginator[PlaylistItem]  # pyright: ignore[reportIncompatibleVariableOverride]
    """The tracks of the playlist."""


class PlaylistTracks(BaseModel):
    """Link to the Web API endpoint where full details of the playlist's tracks can be retrieved,
    along with the total number of tracks in the playlist. Note, a track object may be [`None`][].
    This can happen if a track is no longer available.
    """

    href: str
    """A link to the Web API endpoint where full details of the playlist's tracks can be retrieved."""
    total: int
    """Number of tracks in the playlist."""


class PlaylistItem(BaseModel):
    """A playlist item."""

    added_at: datetime.datetime | None
    """The date and time the track or episode was added.
    
    !!! note
        Some very old playlists may return [`None`][] in this field.
    """
    added_by: SimpleUser | None
    """The Spotify user who added the track or episode.
    
    !!! note
        Some very old playlists may return [`None`][] in this field.
    """
    is_local: bool
    """Whether this track or episode is a local file or not."""
    item: TrackWithSimpleArtist | Episode | None
    """Information about the track or episode."""


class Playlists(BaseModel):
    """A set of playlists."""

    message: str
    """The localized message of a playlist. e.g. 'Popular Playlists'"""
    playlists: Paginator[SimplePlaylist]
    """The playlists in the set."""


class BasePaginator(
    BaseModel,
    typing.Generic[T],
):
    """A paginator with helpful methods to iterate through large amounts of content."""

    href: str
    """A link to the Web API endpoint returning the full result of the request."""
    limit: int
    """The maximum number of items in the response."""
    next: str | None
    """URL to the next page of items."""
    total: int
    """The total number of items available to return."""
    items: list[T]
    """The requested content."""

    # TODO: add abstract methods here which are covered in the subclasses


class Paginator(BasePaginator[T]):
    """A basic paginator."""

    offset: int
    """The offset of the items returned."""
    previous: str | None
    """URL to the previous page of items."""


class CursorPaginator(BasePaginator[T]):
    """A paginator using cursors to paginate the content."""

    cursors: Cursors
    """The cursors used to find the next set of items."""
    total: int | None = None  # pyright: ignore[reportIncompatibleVariableOverride]
    """The total number of items available to return."""


class Cursors(BaseModel):
    """Cursors used to find the next/previous set of items in a paginator."""

    after: str | None = None
    """The cursor to use as key to find the next page of items."""
    before: str | None = None
    """The cursor to use as key to find the previous page of items."""


class Restrictions(BaseModel):
    """Content restrictions."""

    reason: enums.Reason
    """The reason for the restriction."""

    @pydantic.field_validator("reason", mode="before", check_fields=False)
    @classmethod
    def reason_validator(cls, v: str) -> str:
        return v if v in ("market", "product", "explicit", "payment_required") else "unknown"


class ResumePoint(BaseModel):
    """Resume point information."""

    fully_played: bool
    """Whether or not the episode has been fully played by the user."""
    resume_position: datetime.timedelta = pydantic.Field(alias="resume_position_ms")
    """The user's most recent position in the episode."""

    @pydantic.field_validator("resume_position", mode="before", check_fields=False)
    @classmethod
    def resume_position_validator(cls, v: int) -> float:
        return v / 1000


class SavedShow(BaseModel):
    """Information about a show saved to a user's 'Your Music' library."""

    added_at: datetime.datetime
    """The date and time the show was saved."""
    show: SimpleShow
    """The show."""


class SimpleShow(BaseModel):
    """A simplified show."""

    available_markets: list[str]
    """A list of the countries in which the show can be played, identified by their
    [ISO 3166-1 alpha-2 code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
    """
    copyrights: list[Copyright]
    """The copyright statements of the show."""
    description: str
    """A description of the show. HTML tags are stripped away from this field, use the
    [`html_description`][spotify.models.Show.html_description] field in case HTML tags are needed.
    """
    html_description: str
    """A description of the show. This field may contain HTML tags."""
    explicit: bool
    """Whether or not the show has explicit content."""
    external_urls: ExternalURLs
    """External URLs for the show."""
    href: str
    """A link to the Web API endpoint providing full details of the show."""
    id: str
    """The Spotify ID for the show."""
    images: list[Image]
    """The cover art for the show in various sizes, widest first."""
    is_externally_hosted: bool | None
    """[`True`][] if all of the shows episodes are hosted outside of Spotify's CDN. This field might be
    [`None`][] in some cases.
    """
    languages: list[str]
    """A list of the languages used in the show, identified by their 
    [ISO 639 code](https://en.wikipedia.org/wiki/ISO_639).
    """
    media_type: str
    """The media type of the show."""
    name: str
    """The name of the episode."""
    publisher: str
    """The publisher of the show."""
    uri: str
    """The Spotify URI for the show."""
    total_episodes: int
    """The total number of episodes in the show."""


class Show(SimpleShow):
    """A show."""

    episodes: Paginator[SimpleEpisode]
    """The episodes of the show."""


class SearchResult(BaseModel):
    """A search result."""

    tracks: Paginator[TrackWithSimpleArtist] | None = None
    """Returned tracks."""
    artists: Paginator[Artist] | None = None
    """Returned artists."""
    albums: Paginator[SimpleAlbum] | None = None
    """Returned albums."""
    playlists: Paginator[SimplePlaylist] | None = None
    """Returned playlists."""
    # NOTE: the unique `SimpleShow | None` below is to ignore/bypass an error caused by the
    # spotify API where it returns `null` objects instead of `Show` objects
    shows: Paginator[SimpleShow | None] | None = None
    """Returned shows."""
    episodes: Paginator[SimpleEpisode] | None = None
    """Returned episodes."""
    audiobooks: Paginator[SimpleAudiobook] | None = None
    """Returned audiobooks."""


class SavedTrack(BaseModel):
    """Information about a track saved to a user's 'Your Music' library."""

    added_at: datetime.datetime
    """The date and time the track was saved."""
    track: TrackWithSimpleArtist
    """The track."""


class LinkedFromTrack(BaseModel):
    """Information about the originally requested track when
    [Track Relinking](https://developer.spotify.com/documentation/web-api/concepts/track-relinking)
    is applied.
    """

    external_urls: ExternalURLs
    """Known external URLs for the track."""
    href: str
    """A link to the Web API endpoint providing full details of the track."""
    id: str
    """The Spotify ID for the track."""
    uri: str
    """The Spotify URI for the track."""


class TrackBase(LinkedFromTrack, DurationMS, typing.Generic[ArtistT]):
    """Base class for a track."""

    artists: list[ArtistT]
    """The artists who performed the track."""
    available_markets: list[str] | None = None
    """A list of the countries in which the track can be played, identified by their
    [ISO 3166-1 alpha-2 code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
    """
    disc_number: int
    """The disc number (usually `1` unless the album consists of more than one disc)."""
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
    """The track length."""
    explicit: bool
    """Whether or not the track has explicit lyrics."""
    is_playable: bool | None = None
    """Whether or not the track is playable in the given market. Present when
    [Track Relinking](https://developer.spotify.com/documentation/web-api/concepts/track-relinking)
    is applied.
    """
    linked_from: LinkedFromTrack | None = None
    """Present when
    [Track Relinking](https://developer.spotify.com/documentation/web-api/concepts/track-relinking)
    is applied, and the requested track has been replaced with a different track. The track in the
    [`linked_from`][spotify.models.TrackBase.linked_from] object contains information about the
    originally requested track.
    """
    restrictions: Restrictions | None = None
    """Present when restrictions are applied to the track."""
    name: str
    """The name of the track."""
    preview_url: str | None
    """A link to a 30 second preview (MP3 format) of the track. Can be [`None`][]."""
    track_number: int
    """The number of the track. If an album has several discs, the track number is the number on
    the specified disc.
    """
    is_local: bool
    """Whether or not the track is from a local file."""


class SimpleTrack(TrackBase[SimpleArtist]):
    """A simplified track."""


class FullTrack(TrackBase[ArtistT], typing.Generic[ArtistT]):
    """A track class with all available track attributes."""

    album: SimpleAlbum
    """The album on which the track appears."""
    external_ids: ExternalIDs
    """Known external IDs for the track."""
    popularity: int
    """The popularity of the track. The value will be between `0` and `100`, with `100` being the
    most popular.
    """


class Track(FullTrack[Artist]):
    """A track."""


class TrackWithSimpleArtist(FullTrack[SimpleArtist]):
    """A track where the [`artist`][spotify.models.TrackWithSimpleArtist.artist] field is a
    [`SimpleArtist`][spotify.models.SimpleArtist] object.
    """


class SimpleUser(BaseModel):
    """A simplified user."""

    external_urls: ExternalURLs
    """Known external URLs for the user."""
    followers: Followers | None = None
    """Information about the followers of the user."""
    href: str
    """A link to the Web API endpoint for the user."""
    id: str
    """The Spotify user ID for the user."""
    uri: str
    """The Spotify URI for the user."""


class User(SimpleUser):
    """A user."""

    display_name: str | None
    """The name displayed on the user's profile. [`None`][] if not available."""


class OwnUser(User):
    """A user with additional information."""

    country: str | None = None
    """The country of the user, as set in the user's account profile. An
    [ISO 3166-1 alpha-2 country code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
    This field is only available when the current user has granted access to the
    [`USER_READ_PRIVATE`][spotify.enums.Scope.USER_READ_PRIVATE] scope.
    """
    email: str | None = None
    """The user's email address, as entered by the user when creating their account.
    This field is only available when the current user has granted access to the
    [`USER_READ_EMAIL`][spotify.enums.Scope.USER_READ_EMAIL] scope.
    
    !!! warning 
        This email address is unverified; there is no proof that it actually belongs to the user.
    """
    explicit_content: ExplicitContent | None = None
    """The user's explicit content settings. This field is only available when the current user
    has granted access to the [`USER_READ_PRIVATE`][spotify.enums.Scope.USER_READ_PRIVATE] scope.
    """
    images: list[Image]
    """The user's profile image."""
    product: enums.SubscriptionLevel | None = None
    """The user's Spotify subscription level. This field is only available when the current user
    has granted access to the [`USER_READ_PRIVATE`][spotify.enums.Scope.USER_READ_PRIVATE] scope.
    """

    @pydantic.field_validator("product", mode="before", check_fields=False)
    @classmethod
    def product_validator(cls, v: str) -> str:
        return "free" if v == "open" else v


class Recommendations(BaseModel):
    """Recommendations."""

    seeds: list[RecommendationSeed]
    """A list of recommendation seeds."""
    tracks: list[Track]
    """A list of tracks."""


class RecommendationSeed(BaseModel):
    """A recommendation seed."""

    after_filtering_size: int
    """The number of tracks available after `min` and `max` filters have been applied."""
    after_relinking_size: int
    """The number of tracks available after relinking for regional availability."""
    href: str | None
    """A link to the full track or artist data for the seed.
    
    * For tracks this will be a link to a [`Track`][spotify.models.Track] object.
    * For artists a link to an [`Artist`][spotify.models.Artist] object.
    * For genre seeds, this value will be [`None`][].
    """
    id: str
    """The id used to select the seed. This will be the same as the string used in the
    `seed_artists`, `seed_tracks` or `seed_genres`
    [parameter][spotify.rest.API.get_recommendations]."""
    initial_pool_size: int
    """The number of recommended tracks available for the seed."""
    type: enums.RecommendationSeedType
    """The entity type of the seed."""


# MIT License
#
# Copyright (c) 2022-present novanai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
