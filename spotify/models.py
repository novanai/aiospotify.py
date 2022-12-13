from __future__ import annotations

import abc
import datetime
import typing

import attrs

from spotify import enums, utils


class ModelBase(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ModelBase:
        ...


ModelT = typing.TypeVar("ModelT", bound=ModelBase)


@attrs.frozen
class Album(ModelBase):
    """An album."""

    album_type: enums.AlbumType
    """The type of the album."""
    total_tracks: int
    """The number of tracks in the album."""
    available_markets: list[str] | None
    """The markets in which the album is available
    (`ISO 3166-1 alpha-2 country codes <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_).
    Returns ``None`` if a market was specified in the request.
    
    .. note::
        An album is considered available in a market when at least 1 of its tracks is available
        in that market."""
    external_urls: ExternalURLs
    """Known external URLs for this album."""
    href: str
    """A link to the Web API endpoint providing full details of the album."""
    id: str
    """The Spotify ID for the album."""
    images: list[Image]
    """The cover art for the album in various sizes, widest first."""
    name: str
    """The name of the album."""
    release_date: datetime.datetime
    """The date the album was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which ``release_date`` is known."""
    restrictions: Restrictions | None
    """Present when a content restriction is applied."""
    uri: str
    """The Spotify URI for the album."""
    artists: list[Artist]
    """The artists of the album."""
    album_group: enums.AlbumGroup | None
    """Represents the relationship between the artist and the album. 
    Present when getting an artist's albums."""
    tracks: Paginator[Track] | None
    """The tracks of the album."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Album:
        return cls(
            enums.AlbumType(payload["album_type"]),
            payload["total_tracks"],
            payload.get("available_markets"),
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload["name"],
            utils.datetime_from_timestamp(payload["release_date"]),
            enums.ReleaseDatePrecision(payload["release_date_precision"]),
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            payload["uri"],
            [Artist.from_payload(ar) for ar in payload["artists"]],
            payload.get("album_group"),
            Paginator.from_payload(tra, Track)
            if (tra := payload.get("tracks"))
            else None,
        )


@attrs.frozen
class Artist(ModelBase):
    """An artist."""

    external_urls: ExternalURLs
    """Known external URLs for this artist."""
    followers: Followers | None
    """Information about the followers of the artist."""
    genres: list[str]  # list[Genre] if I can find list of all possible genres
    """A list of the genres the artist is associated with. If not yet classified, the list is empty."""
    href: str
    """A link to the Web API endpoint providing full details of the artist."""
    id: str
    """The Spotify ID for the artist."""
    images: list[Image]
    """Images of the artist in various sizes, widest first."""
    name: str
    """The name of the artist."""
    popularity: int | None
    """The popularity of the artist. The value will be between 0 and 100, with 100 being the most
    popular. The artist's popularity is calculated from the popularity of all the artist's tracks."""
    uri: str
    """The Spotify URI for the artist."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Artist:
        return cls(
            ExternalURLs.from_payload(payload["external_urls"]),
            Followers.from_payload(fol) if (fol := payload.get("followers")) else None,
            payload.get("genres", []),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload.get("images", [])],
            payload["name"],
            payload.get("popularity"),
            payload["uri"],
        )


@attrs.frozen
class AudioAnalysis(ModelBase):
    """Track audio analysis."""

    meta: AudioAnalysisMeta
    """Metadata."""
    track: AudioAnalysisTrack
    """Track information"""
    bars: list[AudioAnalysisBar]
    """The time intervals of the bars throughout the track."""
    beats: list[AudioAnalysisBeat]
    """The time intervals of beats throughout the track. """
    sections: list[AudioAnalysisSection]
    """Sections are defined by large variations in rhythm or timbre, e.g. chorus, verse, bridge,
    guitar solo, etc. Each section contains its own descriptions of tempo, key, mode, time_signature,
    and loudness."""
    segments: list[AudioAnalysisSegment]
    """Each segment contains a roughly consistent sound throughout its duration."""
    tatums: list[AudioAnalysisTatum]
    """A tatum represents the lowest regular pulse train that a listener intuitively infers from the
    timing of perceived musical events (segments)."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysis:
        return cls(
            AudioAnalysisMeta.from_payload(payload["meta"]),
            AudioAnalysisTrack.from_payload(payload["track"]),
            [AudioAnalysisBar.from_payload(bar) for bar in payload["bars"]],
            [AudioAnalysisBeat.from_payload(bea) for bea in payload["beats"]],
            [AudioAnalysisSection.from_payload(sec) for sec in payload["sections"]],
            [AudioAnalysisSegment.from_payload(seg) for seg in payload["segments"]],
            [AudioAnalysisTatum.from_payload(tat) for tat in payload["tatums"]],
        )


@attrs.frozen
class AudioAnalysisMeta(ModelBase):
    """Audio analysis metadata."""

    analyzer_version: str
    """The version of the Analyzer used to analyze this track."""
    platform: str
    """The platform used to read the track's audio data."""
    detailed_status: str
    """A detailed status code for this track. If analysis data is missing, this code may explain why."""
    status_code: int
    """The return code of the analyzer process. ``0`` if successful, ``1`` if any errors occurred."""
    timestamp: datetime.datetime
    """The time at which this track was analyzed."""
    analysis_time: datetime.timedelta
    """The amount of time taken to analyze this track."""
    input_process: str
    """The method used to read the track's audio data."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisMeta:
        return cls(
            payload["analyzer_version"],
            payload["platform"],
            payload["detailed_status"],
            payload["status_code"],
            datetime.datetime.fromtimestamp(payload["timestamp"]),
            datetime.timedelta(seconds=payload["analysis_time"]),
            payload["input_process"],
        )


@attrs.frozen
class AudioAnalysisTrack(ModelBase):
    """Audio analysis track information."""

    num_samples: int
    """The exact number of audio samples analyzed from this track. See also analysis_sample_rate."""
    duration: float
    """Length of the track in seconds."""
    sample_md5: str
    """This field will always contain the empty string."""
    offset_seconds: int
    """An offset to the start of the region of the track that was analyzed. (As the entire track is
    analyzed, this should always be 0.)"""
    window_seconds: int
    """The length of the region of the track was analyzed, if a subset of the track was analyzed.
    (As the entire track is analyzed, this should always be 0.)"""
    analysis_sample_rate: int
    """The sample rate used to decode and analyze this track. May differ from the actual sample rate
    of this track available on Spotify."""
    analysis_channels: int
    """The number of channels used for analysis. If 1, all channels are summed together to mono before
    analysis."""
    end_of_fade_in: float
    """The time, in seconds, at which the track's fade-in period ends. If the track has no fade-in,
    this will be 0.0."""
    start_of_fade_out: float
    """The time, in seconds, at which the track's fade-out period starts. If the track has no fade-out,
    this should match the track's length."""
    loudness: float
    """The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire
    track and are useful for comparing relative loudness of tracks. Loudness is the quality of a sound
    that is the primary psychological correlate of physical strength (amplitude). Values typically range
    between -60 and 0 db."""
    tempo: float
    """The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo
    is the speed or pace of a given piece and derives directly from the average beat duration."""
    tempo_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the tempo."""
    time_signature: int
    """An estimated time signature. The time signature (meter) is a notational convention to specify
    how many beats are in each bar (or measure). The time signature ranges from 3 to 7 indicating time
    signatures of "3/4", to "7/4"."""
    time_signature_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the time_signature."""
    key: int
    """The key the track is in. Integers map to pitches using standard
    `Pitch Class notation <https://en.wikipedia.org/wiki/Pitch_class>`_. E.g. 0 = C, 1 = C♯/D♭, 2 = D,
    and so on. If no key was detected, the value is -1."""
    key_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the key."""
    mode: int
    """Mode indicates the modality (major or minor) of a track, the type of scale from which its melodic
    content is derived. Major is represented by 1 and minor is 0."""
    mode_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the mode."""
    codestring: str
    """An `Echo Nest Musical Fingerprint (ENMFP) <https://academiccommons.columbia.edu/doi/10.7916/D8Q248M4>`_
    codestring for this track."""
    code_version: float
    """A version number for the Echo Nest Musical Fingerprint format used in the codestring field."""
    echoprintstring: str
    """An `EchoPrint <https://github.com/spotify/echoprint-codegen>`_ codestring for this track."""
    echoprint_version: float
    """A version number for the EchoPrint format used in the echoprintstring field."""
    synchstring: str
    """A `Synchstring <https://github.com/echonest/synchdata>`_ for this track."""
    synch_version: float
    """A version number for the Synchstring used in the synchstring field."""
    rhythmstring: str
    """A Rhythmstring for this track. The format of this string is similar to the Synchstring."""
    rhythm_version: float
    """A version number for the Rhythmstring used in the rhythmstring field."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisTrack:
        return cls(
            payload["num_samples"],
            payload["duration"],
            payload["sample_md5"],
            payload["offset_seconds"],
            payload["window_seconds"],
            payload["analysis_sample_rate"],
            payload["analysis_channels"],
            payload["end_of_fade_in"],
            payload["start_of_fade_out"],
            payload["loudness"],
            payload["tempo"],
            payload["tempo_confidence"],
            payload["time_signature"],
            payload["time_signature_confidence"],
            payload["key"],
            payload["key_confidence"],
            payload["mode"],
            payload["mode_confidence"],
            payload["codestring"],
            payload["code_version"],
            payload["echoprintstring"],
            payload["echoprint_version"],
            payload["synchstring"],
            payload["synch_version"],
            payload["rhythmstring"],
            payload["rhythm_version"],
        )


@attrs.frozen
class AudioAnalysisBar(ModelBase):
    """Audio analysis of a bar.
    A bar (or measure) is a segment of time defined as a given number of beats."""

    start: float
    """The starting point (in seconds) of the time interval."""
    duration: float
    """The duration (in seconds) of the time interval."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the interval."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisBar:
        return cls(
            payload["start"],
            payload["duration"],
            payload["confidence"],
        )


@attrs.frozen
class AudioAnalysisBeat(ModelBase):
    """Audio analysis of a beat.
    A beat is the basic time unit of a piece of music; for example, each tick of a metronome.
    Beats are typically multiples of tatums."""

    start: float
    """The starting point (in seconds) of the time interval."""
    duration: float
    """The duration (in seconds) of the time interval."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the interval."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisBeat:
        return cls(
            payload["start"],
            payload["duration"],
            payload["confidence"],
        )


@attrs.frozen
class AudioAnalysisSection(ModelBase):
    """Audio analysis of a section.
    Sections are defined by large variations in rhythm or timbre, e.g. chorus, verse, bridge, guitar
    solo, etc. Each section contains its own descriptions of tempo, key, mode, time_signature, and
    loudness."""

    start: float
    """The starting point (in seconds) of the section."""
    duration: float
    """The duration (in seconds) of the section."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the section's "designation"."""
    loudness: float
    """The overall loudness of the section in decibels (dB). Loudness values are useful for comparing
    relative loudness of sections within tracks."""
    tempo: float
    """The overall estimated tempo of the section in beats per minute (BPM). In musical terminology,
    tempo is the speed or pace of a given piece and derives directly from the average beat duration."""
    tempo_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the tempo. Some tracks contain tempo
    changes or sounds which don't contain tempo (like pure speech) which would correspond to a low
    value in this field."""
    key: int
    """The estimated overall key of the section. The values in this field ranging from 0 to 11 mapping
    to pitches using standard Pitch Class notation (E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on). If no key
    was detected, the value is -1."""
    key_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the key. Songs with many key changes may
    correspond to low values in this field."""
    mode: float
    """Indicates the modality (major or minor) of a section, the type of scale from which its melodic
    content is derived. This field will contain a 0 for "minor", a 1 for "major", or a -1 for no result.
    Note that the major key (e.g. C major) could more likely be confused with the minor key at 3
    semitones lower (e.g. A minor) as both keys carry the same pitches."""
    mode_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the mode."""
    time_signature: int
    """An estimated time signature. The time signature (meter) is a notational convention to specify
    how many beats are in each bar (or measure). The time signature ranges from 3 to 7 indicating time
    signatures of "3/4", to "7/4"."""
    time_signature_confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the time_signature. Sections with time
    signature changes may correspond to low values in this field."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisSection:
        return cls(
            payload["start"],
            payload["duration"],
            payload["confidence"],
            payload["loudness"],
            payload["tempo"],
            payload["tempo_confidence"],
            payload["key"],
            payload["key_confidence"],
            payload["mode"],
            payload["mode_confidence"],
            payload["time_signature"],
            payload["time_signature_confidence"],
        )


@attrs.frozen
class AudioAnalysisSegment(ModelBase):
    """Audio analysis segment."""

    start: float
    """The starting point (in seconds) of the segment."""
    duration: float
    """The duration (in seconds) of the segment."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the segmentation. Segments of the song
    which are difficult to logically segment (e.g: noise) may correspond to low values in this field."""
    loudness_start: float
    """The onset loudness of the segment in decibels (dB). Combined with loudness_max and
    loudness_max_time, these components can be used to describe the "attack" of the segment."""
    loudness_max: float
    """The peak loudness of the segment in decibels (dB). Combined with loudness_start and
    loudness_max_time, these components can be used to describe the "attack" of the segment."""
    loudness_max_time: float
    """The segment-relative offset of the segment peak loudness in seconds. Combined with loudness_start
    and loudness_max, these components can be used to desctibe the "attack" of the segment."""
    loudness_end: float
    """The offset loudness of the segment in decibels (dB). This value should be equivalent to the
    loudness_start of the following segment."""
    pitches: list[float]
    """Pitch content is given by a “chroma” vector, corresponding to the 12 pitch classes C, C#, D to B,
    with values ranging from 0 to 1 that describe the relative dominance of every pitch in the chromatic
    scale. For example a C Major chord would likely be represented by large values of C, E and G (i.e.
    classes 0, 4, and 7).

    Vectors are normalized to 1 by their strongest dimension, therefore noisy sounds are likely
    represented by values that are all close to 1, while pure tones are described by one value at 1
    (the pitch) and others near 0. As can be seen below, the 12 vector indices are a combination of
    low-power spectrum values at their respective pitch frequencies.
    
    .. image:: https://developer.spotify.com/assets/audio/Pitch_vector.png"""
    timbre: list[float]
    """Timbre is the quality of a musical note or sound that distinguishes different types of musical
    instruments, or voices. It is a complex notion also referred to as sound color, texture, or tone 
    quality, and is derived from the shape of a segment's spectro-temporal surface, independently of
    pitch and loudness. The timbre feature is a vector that includes 12 unbounded values roughly
    centered around 0. Those values are high level abstractions of the spectral surface, ordered by
    degree of importance.

    For completeness however, the first dimension represents the average loudness of the segment; 
    second emphasizes brightness; third is more closely correlated to the flatness of a sound; fourth
    to sounds with a stronger attack; etc. See an image below representing the 12 basis functions (i.e.
    template segments).

    .. image:: https://developer.spotify.com/assets/audio/Timbre_basis_functions.png

    The actual timbre of the segment is best described as a linear combination of these 12 basis
    functions weighted by the coefficient values: timbre = c1 x b1 + c2 x b2 + ... + c12 x b12, where
    c1 to c12 represent the 12 coefficients and b1 to b12 the 12 basis functions as displayed below.
    Timbre vectors are best used in comparison with each other."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisSegment:
        return cls(
            payload["start"],
            payload["duration"],
            payload["confidence"],
            payload["loudness_start"],
            payload["loudness_max"],
            payload["loudness_max_time"],
            payload["loudness_end"],
            payload["pitches"],
            payload["timbre"],
        )


@attrs.frozen
class AudioAnalysisTatum(ModelBase):
    """Audio analysis tatum.

    A tatum represents the lowest regular pulse train that a listener intuitively infers from the timing
    of perceived musical events (segments)."""

    start: float
    """The starting point (in seconds) of the time interval."""
    duration: float
    """The duration (in seconds) of the time interval."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the interval."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioAnalysisTatum:
        return cls(
            payload["start"],
            payload["duration"],
            payload["confidence"],
        )


@attrs.frozen
class Audiobook(ModelBase):
    """An audiobook."""

    authors: list[Author]
    """The author(s) for the audiobook."""
    available_markets: list[str]
    """A list of the countries in which the audiobook can be played, identified by their
    `ISO 3166-1 alpha-2 code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_."""
    copyrights: list[Copyright]
    """The copyright statements of the audiobook."""
    description: str
    """A description of the audiobook. HTML tags are stripped away from this field, use the
    ``models.Audiobook.html_description`` field in case HTML tags are needed."""
    html_description: str
    """A description of the audiobook. This field may contain HTML tags."""
    explicit: bool
    """Whether or not the audiobook has explicit content."""
    external_urls: ExternalURLs
    """External URLs for this audiobook."""
    href: str
    """A link to the Web API endpoint providing full details of the audiobook."""
    id: str
    """The Spotify ID for the audiobook."""
    images: list[Image]
    """The cover art for the audiobook in various sizes, widest first."""
    languages: list[str]
    """A list of the languages used in the audiobook, identified by their
    `ISO 639 <https://en.wikipedia.org/wiki/ISO_639>`_ code."""
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
    total_chapters: int
    """The number of chapters in this audiobook."""
    chapters: Paginator[Chapter] | None
    """The chapters of the audiobook. Not available when fetching several audiobooks or fetching
    a specific chapter."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Audiobook:
        return cls(
            [Author.from_payload(aut) for aut in payload["authors"]],
            payload["available_markets"],
            [Copyright.from_payload(cop) for cop in payload["copyrights"]],
            payload["description"],
            payload["html_description"],
            payload["explicit"],
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload["languages"],
            payload["media_type"],
            payload["name"],
            [Narrator.from_payload(nar) for nar in payload["narrators"]],
            payload["publisher"],
            payload["uri"],
            payload["total_chapters"],
            Paginator.from_payload(cha, Chapter)
            if (cha := payload.get("chapters"))
            else None,
        )


@attrs.frozen
class AudioFeatures(ModelBase):
    """Track audio features."""

    acousticness: float
    """A confidence measure from ``0.0`` to ``1.0`` of whether the track is acoustic. 
    ``1.0`` represents high confidence the track is acoustic."""
    analysis_url: str
    """A URL to access the full audio analysis of this track.
    An access token is required to access this data."""
    danceability: float
    """Danceability describes how suitable a track is for dancing based on a combination of
    musical elements including tempo, rhythm stability, beat strength, and overall regularity.
    A value of ``0.0`` is least danceable and ``1.0`` is most danceable."""
    duration: datetime.timedelta
    """The duration of the track."""
    energy: float
    """Energy is a measure from ``0.0`` to ``1.0`` and represents a perceptual measure of intensity and activity.
    Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy,
    while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute
    include dynamic range, perceived loudness, timbre, onset rate, and general entropy."""
    id: str
    """The Spotify ID for the track."""
    instrumentalness: float
    """Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental in 
    this context. Rap or spoken word tracks are clearly "vocal". The closer the instrumentalness value is 
    to ``1.0``, the greater likelihood the track contains no vocal content. Values above ``0.5`` are
    intended to represent instrumental tracks, but confidence is higher as the value approaches ``1.0``."""
    key: int
    """The key the track is in. Integers map to pitches using standard
    `Pitch Class notation <https://en.wikipedia.org/wiki/Pitch_class>`_. E.g. ``0`` = C, ``1`` = C♯/D♭,
    ``2`` = D, and so on. If no key was detected, the value is ``-1``."""
    liveness: float
    """Detects the presence of an audience in the recording. Higher liveness values represent an
    increased probability that the track was performed live. A value above ``0.8`` provides strong
    likelihood that the track is live."""
    loudness: float
    """The overall loudness of a track in decibels (dB). Loudness values are averaged across the
    entire track and are useful for comparing relative loudness of tracks. Loudness is the quality
    of a sound that is the primary psychological correlate of physical strength (amplitude). Values
    typically range between ``-60`` and ``0`` db."""
    mode: enums.TrackMode
    """Mode indicates the modality (major or minor) of a track, the type of scale from which its
    melodic content is derived. Major is represented by ``1`` and minor is ``0``."""
    speechiness: float
    """Speechiness detects the presence of spoken words in a track. The more exclusively speech-like
    the recording (e.g. talk show, audio book, poetry), the closer to ``1.0`` the attribute value. Values
    above ``0.66`` describe tracks that are probably made entirely of spoken words. Values between
    ``0.33`` and ``0.66`` describe tracks that may contain both music and speech, either in sections or
    layered, including such cases as rap music. Values below ``0.33`` most likely represent music and 
    other non-speech-like tracks."""
    tempo: float
    """The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo
    is the speed or pace of a given piece and derives directly from the average beat duration."""
    time_signature: int
    """An estimated time signature. The time signature (meter) is a notational convention to specify
    how many beats are in each bar (or measure). The time signature ranges from ``3`` to ``7`` indicating
    time signatures of "3/4", to "7/4"."""
    track_href: str
    """A link to the Web API endpoint providing full details of the track."""
    uri: str
    """The Spotify URI for the track."""
    valence: float
    """A measure from ``0.0`` to ``1.0`` describing the musical positiveness conveyed by a track. Tracks
    with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence
    sound more negative (e.g. sad, depressed, angry)."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> AudioFeatures:
        return cls(
            payload["acousticness"],
            payload["analysis_url"],
            payload["danceability"],
            datetime.timedelta(milliseconds=payload["duration_ms"]),
            payload["energy"],
            payload["id"],
            payload["instrumentalness"],
            payload["key"],
            payload["liveness"],
            payload["loudness"],
            enums.TrackMode(payload["mode"]),
            payload["speechiness"],
            payload["tempo"],
            payload["time_signature"],
            payload["track_href"],
            payload["uri"],
            payload["valence"],
        )


@attrs.frozen
class Author(ModelBase):
    """Author information."""

    name: str
    """The name of the author."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Author:
        return cls(
            payload["name"],
        )


@attrs.frozen
class Chapter(ModelBase):
    """A chapter."""

    audio_preview_url: str | None
    """A URL to a 30 second preview (MP3 format) of the chapter. ``None`` if not available."""
    chapter_number: int
    """The number of the chapter."""
    description: str
    """A description of the chapter. HTML tags are stripped away from this field, use the ``html_description`` field in case HTML tags are needed."""
    html_description: str
    """A description of the chapter. This field may contain HTML tags."""
    duration: datetime.timedelta
    """The chapter length."""
    explicit: bool
    """Whether or not the chapter has explicit content."""
    external_urls: ExternalURLs
    """External URLs for this chapter."""
    href: str
    """A link to the Web API endpoint providing full details of the chapter."""
    id: str
    """The Spotify ID for the chapter."""
    images: list[Image]
    """The cover art for the chapter in various sizes, widest first."""
    is_playable: bool
    """True if the chapter is playable in the given market. Otherwise false."""
    languages: list[str]
    """A list of the languages used in the chapter, identified by their `ISO 639-1 code <https://en.wikipedia.org/wiki/ISO_639>`_."""
    name: str
    """The name of the chapter."""
    release_date: datetime.datetime
    """The date the chapter was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which ``release_date`` value is known."""
    resume_point: ResumePoint | None
    """The user's most recent position in the chapter. Set if the supplied access token is a user token and has the scope 'user-read-playback-position'."""
    uri: str
    """The Spotify URI for the chapter."""
    restrictions: Restrictions | None
    """Present when a content restriction is applied."""
    audiobook: Audiobook | None
    """The audiobook on which this chapter appears. Not present when fetching an audiobook."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Chapter:
        return cls(
            payload["audio_preview_url"],
            payload["chapter_number"],
            payload["description"],
            payload["html_description"],
            datetime.timedelta(milliseconds=payload["duration_ms"]),
            payload["explicit"],
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload["is_playable"],
            payload["languages"],
            payload["name"],
            utils.datetime_from_timestamp(payload["release_date"]),
            enums.ReleaseDatePrecision(payload["release_date_precision"]),
            ResumePoint.from_payload(res)
            if (res := payload.get("resume_point"))
            else None,
            payload["uri"],
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            Audiobook.from_payload(aud) if (aud := payload.get("audiobook")) else None,
        )


@attrs.frozen
class Copyright(ModelBase):
    """Copyright statements."""

    text: str
    """The copyright text for this content."""
    type: enums.CopyrightType
    """The type of copyright."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Copyright:
        return cls(
            payload["text"],
            enums.CopyrightType(payload["type"]),
        )


@attrs.frozen
class Episode(ModelBase):
    """An episode."""

    audio_preview_url: str | None
    """A URL to a 30 second preview (MP3 format) of the episode. ``None`` if not available."""
    description: str
    """A description of the episode. HTML tags are stripped away from this field, use the ``html_description`` field in case HTML tags are needed."""
    html_description: str
    """A description of the episode. This field may contain HTML tags."""
    duration: datetime.timedelta
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
    """True if the episode is hosted outside of Spotify's CDN."""
    is_playable: bool
    """True if the episode is playable in the given market. Otherwise false."""
    languages: list[str]
    """A list of the languages used in the episode, identified by their `ISO 639-1 code <https://en.wikipedia.org/wiki/ISO_639>`_."""
    name: str
    """The name of the episode."""
    release_date: datetime.datetime
    """The date the episode was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which ``release_date`` value is known."""
    resume_point: ResumePoint | None
    """The user's most recent position in the episode. Set if the supplied access token is a user token and has the scope 'user-read-playback-position'."""
    uri: str
    """The Spotify URI for the episode."""
    restrictions: Restrictions | None
    """Present when a content restriction is applied."""
    show: Show | None
    """The show on which this episode appears. Not present when fetching a show."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Episode:
        return cls(
            payload["audio_preview_url"],
            payload["description"],
            payload["html_description"],
            datetime.timedelta(milliseconds=payload["duration_ms"]),
            payload["explicit"],
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload["is_externally_hosted"],
            payload["is_playable"],
            payload["languages"],
            payload["name"],
            utils.datetime_from_timestamp(payload["release_date"]),
            enums.ReleaseDatePrecision(payload["release_date_precision"]),
            ResumePoint.from_payload(res)
            if (res := payload.get("resume_point"))
            else None,
            payload["uri"],
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            Show.from_payload(sho) if (sho := payload.get("show")) else None,
        )


@attrs.frozen
class ExplicitContent(ModelBase):
    """Explicit content settings."""

    filter_enabled: bool
    """When ``True``, indicates that explicit content should not be played."""
    filter_locked: bool
    """When ``True``, indicates that the explicit content setting is locked and can't be changed by the user."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ExplicitContent:
        return cls(
            payload["filter_enabled"],
            payload["filter_locked"],
        )


@attrs.frozen
class ExternalIDs(ModelBase):
    """External IDs."""

    isrc: str
    """`International Standard Recording Code <http://en.wikipedia.org/wiki/International_Standard_Recording_Code/>`_"""
    ean: str | None
    """`International Article Number <https://en.wikipedia.org/wiki/International_Article_Number_%28EAN%29>`_"""
    upc: str | None
    """`Universal Product Code <http://en.wikipedia.org/wiki/Universal_Product_Code>`_"""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ExternalIDs:
        return cls(
            payload["isrc"],
            payload.get("ean"),
            payload.get("upc"),
        )


@attrs.frozen
class ExternalURLs(ModelBase):
    """External URLs"""

    spotify: str
    """The Spotify URL for the object."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ExternalURLs:
        return cls(payload["spotify"])


@attrs.frozen
class Followers(ModelBase):
    """Information about followers."""

    href: str
    """This will always be set to ``None``, as the Web API does not support it at the moment."""
    total: int
    """The total number of followers."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Followers:
        return cls(
            payload["href"],
            payload["total"],
        )


@attrs.frozen
class Image(ModelBase):
    """An image."""

    url: str
    """The source URL of the image."""
    height: int
    """The image height in pixels."""
    width: int
    """The image width in pixels."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Image:
        return cls(
            payload["url"],
            payload["height"],
            payload["width"],
        )


@attrs.frozen
class Narrator(ModelBase):
    """Author information."""

    name: str
    """The name of the narrator."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Narrator:
        return cls(
            payload["name"],
        )


@attrs.frozen
class Recommendation(ModelBase):
    """Recommendations."""

    seeds: list[RecommendationSeed]
    """A list of recommendation seed objects."""
    tracks: list[RecommendationTrack]
    """A list of simplified track objects."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Recommendation:
        return cls(
            [RecommendationSeed.from_payload(see) for see in payload["seeds"]],
            [RecommendationTrack.from_payload(tra) for tra in payload["tracks"]],
        )


@attrs.frozen
class RecommendationSeed(ModelBase):
    """A recommendation seed."""

    after_filtering_size: int
    """The number of tracks available after min and max filters have been applied."""
    after_relinking_size: int
    """The number of tracks available after relinking for regional availability."""
    href: str | None
    """A link to the full track or artist data for this seed.
    For tracks this will be a link to a Track Object.
    For artists a link to an Artist Object.
    For genre seeds, this value will be ``None``."""
    id: str
    """The id used to select this seed. This will be the same as the string used in the ``seed_artists``, ``seed_tracks`` or
    ``seed_genres`` parameter."""
    initial_pool_size: int
    """The number of recommended tracks available for this seed."""
    type: str
    """The entity type of this seed. One of ``artist``, ``track`` or ``genre``."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> RecommendationSeed:
        return cls(
            payload["afterFilteringSize"],
            payload["afterRelinkingSize"],
            payload["href"],
            payload["id"],
            payload["initialPoolSize"],
            payload["type"],
        )


@attrs.frozen
class RecommendationTrack(ModelBase):
    """A recommendation track."""

    # TODO: It appears album and other fields *are* included with recommendations.

    artists: list[RecommendationArtist]
    """The artists who performed the track."""
    available_markets: list[str] | None
    """A list of the countries in which the track can be played, identified by their `ISO 3166-1 alpha-2 code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
    Returns ``None`` if a market was specified in the request."""
    disc_number: int
    """The disc number (usually ``1`` unless the album consists of more than one disc)."""
    duration: datetime.timedelta
    """The track length."""
    explicit: bool
    """Whether or not the track has explicit lyrics."""
    external_urls: ExternalURLs
    """Known external URLs for this track."""
    href: str
    """A link to the Web API endpoint providing full details of the track."""
    id: str
    """The Spotify ID for the track."""
    is_playable: bool | None
    """Whether or not the track is playable in the given market.
    Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied."""
    linked_from: RecommendationTrack | None
    """Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied, and the requested track has been replaced with a different track.
    The track in the linked_from object contains information about the originally requested track."""
    restrictions: Restrictions | None
    """Present when restrictions are applied to the track."""
    name: str
    """The name of the track."""
    preview_url: str | None
    """A link to a 30 second preview (MP3 format) of the track. Can be ``None``"""
    track_number: int
    """The number of the track. If an album has several discs, the track number is the number on the specified disc."""
    uri: str
    """The Spotify URI for the track."""
    is_local: bool
    """Whether or not the track is from a local file."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> RecommendationTrack:
        return cls(
            [RecommendationArtist.from_payload(art) for art in payload["artists"]],
            payload.get("available_markets"),
            payload["disc_number"],
            datetime.timedelta(milliseconds=payload["duration_ms"]),
            payload["explicit"],
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            payload.get("is_playable"),
            RecommendationTrack.from_payload(tra)
            if (tra := payload.get("linked_from"))
            else None,
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            payload["name"],
            payload["preview_url"],
            payload["track_number"],
            payload["uri"],
            payload["is_local"],
        )


@attrs.frozen
class RecommendationArtist(ModelBase):
    """A recommendation artist."""

    external_urls: ExternalURLs
    """Known external URLs for this artist."""
    href: str
    """A link to the Web API endpoint providing full details of the artist."""
    id: str
    """The Spotify ID for the artist."""
    name: str
    """The name of the artist."""
    uri: str
    """The Spotify URI for the artist."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> RecommendationArtist:
        return cls(
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            payload["name"],
            payload["uri"],
        )


@attrs.frozen
class Restrictions(ModelBase):
    """Content restrictions."""

    reason: enums.Reason
    """The reason for the restriction."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Restrictions:
        return cls(
            enums.Reason.from_payload(payload["reason"]),
        )


@attrs.frozen
class ResumePoint(ModelBase):
    """Resume point information."""

    fully_played: bool
    """Whether or not the episode has been fully played by the user."""
    resume_position: datetime.timedelta
    """The user's most recent position in the episode."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ResumePoint:
        return cls(
            payload["fully_played"],
            datetime.timedelta(milliseconds=payload["resume_position_ms"]),
        )


@attrs.frozen
class Paginator(
    ModelBase,
    typing.Generic[ModelT],
):
    """A paginator with helpful methods to paginate
    through large amounts of content.

    TODO: make those 'helpful methods'"""

    href: str
    """A link to the Web API endpoint returning the full result of the request."""
    items: list[ModelT]
    """The requested content."""
    limit: int
    """The maximum number of items in the response."""
    next: str | None
    """URL to the next page of items."""
    offset: int
    """The offset of the items returned."""
    previous: str | None
    """URL to the previous page of items."""
    total: int
    """The total number of items available to return."""

    @classmethod
    def from_payload(
        cls, payload: dict[str, typing.Any], item_type: typing.Type[ModelT]
    ) -> Paginator[ModelT]:
        return cls(
            payload["href"],
            [item_type.from_payload(itm) for itm in payload["items"]],
            payload["limit"],
            payload["next"],
            payload["offset"],
            payload["previous"],
            payload["total"],
        )


@attrs.frozen
class Show(ModelBase):
    """A show."""

    available_markets: list[str]
    """A list of the countries in which the show can be played, identified by their `ISO 3166-1 alpha-2 code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_."""
    copyrights: list[Copyright]
    """The copyright statements of the show."""
    description: str
    """A description of the show. HTML tags are stripped away from this field, use the ``models.Show.html_description`` field in case HTML tags are needed."""
    html_description: str
    """A description of the show. This field may contain HTML tags."""
    explicit: bool
    """Whether or not the show has explicit content."""
    external_urls: ExternalURLs
    """External URLs for this show."""
    href: str
    """A link to the Web API endpoint providing full details of the show."""
    id: str
    """The Spotify ID for the show."""
    images: list[Image]
    """The cover art for the show in various sizes, widest first."""
    is_externally_hosted: bool | None
    """True if all of the shows episodes are hosted outside of Spotify's CDN. This field might be ``None`` in some cases."""
    languages: list[str]
    """A list of the languages used in the show, identified by their `ISO 639 <https://en.wikipedia.org/wiki/ISO_639>`_ code."""
    media_type: str
    """The media type of the show."""
    name: str
    """The name of the episode."""
    publisher: str
    """The publisher of the show."""
    uri: str
    """The Spotify URI for the show."""
    episodes: Paginator[Episode] | None
    """The episodes of the show. Not available when fetching several shows or fetching a specific episode."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Show:
        return cls(
            payload["available_markets"],
            [Copyright.from_payload(cop) for cop in payload["copyrights"]],
            payload["description"],
            payload["html_description"],
            payload["explicit"],
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload["is_externally_hosted"],
            payload["languages"],
            payload["media_type"],
            payload["name"],
            payload["publisher"],
            payload["uri"],
            Paginator.from_payload(eps, Episode)
            if (eps := payload.get("episodes"))
            else None,
        )


@attrs.frozen
class Track(ModelBase):
    """A track."""

    album: Album | None
    """The album on which the track appears. Will be ``None`` when fetching an album's tracks."""
    artists: list[Artist]
    """The artists who performed the track."""
    available_markets: list[str] | None
    """A list of the countries in which the track can be played, identified by their `ISO 3166-1 alpha-2 code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
    Returns ``None`` if a market was specified in the request."""
    disc_number: int
    """The disc number (usually ``1`` unless the album consists of more than one disc)."""
    duration: datetime.timedelta
    """The track length."""
    explicit: bool
    """Whether or not the track has explicit lyrics."""
    external_ids: ExternalIDs | None
    """Known external IDs for the track."""
    external_urls: ExternalURLs
    """Known external URLs for this track."""
    href: str
    """A link to the Web API endpoint providing full details of the track."""
    id: str
    """The Spotify ID for the track."""
    is_playable: bool | None
    """Whether or not the track is playable in the given market.
    Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied."""
    linked_from: Track | None
    """Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied, and the requested track has been replaced with a different track.
    The track in the linked_from object contains information about the originally requested track."""
    restrictions: Restrictions | None
    """Present when restrictions are applied to the track."""
    name: str
    """The name of the track."""
    popularity: int | None
    """The popularity of the track. The value will be between 0 and 100, with 100 being the most popular."""
    preview_url: str | None
    """A link to a 30 second preview (MP3 format) of the track. Can be ``None``"""
    track_number: int
    """The number of the track. If an album has several discs, the track number is the number on the specified disc."""
    uri: str
    """The Spotify URI for the track."""
    is_local: bool
    """Whether or not the track is from a local file."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Track:
        return cls(
            Album.from_payload(alb) if (alb := payload.get("album")) else None,
            [Artist.from_payload(art) for art in payload["artists"]],
            payload.get("available_markets"),
            payload["disc_number"],
            datetime.timedelta(milliseconds=payload["duration_ms"]),
            payload["explicit"],
            ExternalIDs.from_payload(ext)
            if (ext := payload.get("external_ids"))
            else None,
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            payload.get("is_playable"),
            Track.from_payload(tra) if (tra := payload.get("linked_from")) else None,
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            payload["name"],
            payload.get("popularity"),
            payload["preview_url"],
            payload["track_number"],
            payload["uri"],
            payload["is_local"],
        )


@attrs.frozen
class User(ModelBase):
    """A user."""

    country: str | None
    """The country of the user, as set in the user's account profile. An `ISO 3166-1 alpha-2 country code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_. This field is only available when the current user has granted access to the ``user-read-private`` scope."""
    display_name: str | None
    """The name displayed on the user's profile. ``None`` if not available."""
    email: str | None
    """The user's email address, as entered by the user when creating their account.
    This field is only available when the current user has granted access to the user-read-email scope.
    
    .. warning::

        This email address is unverified; there is no proof that it actually belongs to the user."""
    explicit_content: ExplicitContent | None
    """The user's explicit content settings. This field is only available when the current user has granted access to the user-read-private scope."""
    external_urls: ExternalURLs
    """Known external URLs for this user."""
    followers: Followers
    """Information about the followers of the user."""
    href: str
    """A link to the Web API endpoint for this user."""
    id: str
    """The Spotify user ID for the user."""
    images: list[Image]
    """The user's profile image."""
    product: str | None
    """The user's Spotify subscription level: "premium", "free", etc. (The subscription level "open" can be considered the same as "free".) This field is only available when the current user has granted access to the user-read-private scope."""
    uri: str
    """The Spotify URI for the user."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> User:
        return cls(
            payload.get("country"),
            payload.get("display_name"),
            payload.get("email"),
            ExplicitContent.from_payload(exp)
            if (exp := payload.get("explicit_content"))
            else None,
            ExternalURLs.from_payload(payload["external_urls"]),
            Followers.from_payload(payload["followers"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload.get("product"),
            payload["uri"],
        )
