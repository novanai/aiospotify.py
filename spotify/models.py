from __future__ import annotations

import typing
from spotify import enums, utils
import pydantic
import datetime


ArtistT = typing.TypeVar("ArtistT", bound="SimpleArtist")
T = typing.TypeVar("T")

class BaseModel(pydantic.BaseModel):
    @pydantic.field_validator("release_date", mode="before", check_fields=False)
    @classmethod
    def release_date_validator(cls, v: str) -> datetime.datetime | None:
        if v == "0000":
            return None

        return utils.datetime_from_timestamp(v)
    
    @pydantic.field_validator("duration", mode="before", check_fields=False)
    @classmethod
    def duration_validator(cls, v: int) -> float:
        return v / 1000

    @pydantic.field_validator("album_type", mode="before", check_fields=False)
    @classmethod
    def album_type_validator(cls, v: str):
        return v.lower()

class SavedAlbum(BaseModel):
    """Information about an album saved to a user's "Your Music" library."""

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
    `None` if a market was specified in the request.
    
    > [!note]
    > An album is considered available in a market when at least 1 of its tracks is available in that market.
    """
    external_urls: ExternalURLs
    """Known external URLs for this album."""
    href: str
    """A link to the Web API endpoint providing full details of the album."""
    id: str
    """The Spotify ID for the album."""
    images: list[Image]
    """The cover art for the album in various sizes, widest first."""
    name: str
    """The name of the album. In case of an album takedown, the value may be an empty string."""
    release_date: datetime.date
    """The date the album was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which :obj:`~.Album.release_date` is known."""
    restrictions: Restrictions | None = None
    """Present when a content restriction is applied."""
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
    """The genres the album is associated with. If not yet classified, this sequence is empty."""
    label: str
    """The label associated with the album."""
    popularity: int
    """The popularity of the album. The value will be between 0 and 100, with 100 being the most popular."""

class SimpleArtist(BaseModel):
    """A simplified artist object."""

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

class Artist(SimpleArtist):
    """An artist."""

    followers: Followers
    """Information about the followers of the artist."""
    genres: list[str]
    """A list of the genres the artist is associated with. If not yet classified, the sequence is empty."""
    images: list[Image]
    """Images of the artist in various sizes, widest first."""
    popularity: int
    """The popularity of the artist. The value will be between 0 and 100, with 100 being the most
    popular. The artist's popularity is calculated from the popularity of all the artist's tracks."""

class SimpleAudiobook(BaseModel):
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
    edition: str | None
    """The edition of the audiobook."""
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
    total_chapters: int | None
    """The number of chapters in this audiobook."""

class Audiobook(SimpleAudiobook):
    """An audiobook."""

    chapters: Paginator[SimpleChapter]
    """The chapters of the audiobook."""

class Author(BaseModel):
    """Author information."""

    name: str
    """The name of the author."""

class AudioFeatures(BaseModel):
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
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
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
    # TODO: maybe use an enum for this value?
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


class AudioAnalysis(BaseModel):
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

class AudioAnalysisMeta(BaseModel):
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

class AudioAnalysisTrack(BaseModel):
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

class AudioAnalysisBar(BaseModel):
    """Audio analysis of a bar.
    A bar (or measure) is a segment of time defined as a given number of beats."""

    start: float
    """The starting point (in seconds) of the time interval."""
    duration: float
    """The duration (in seconds) of the time interval."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the interval."""

class AudioAnalysisBeat(BaseModel):
    """Audio analysis of a beat.
    A beat is the basic time unit of a piece of music; for example, each tick of a metronome.
    Beats are typically multiples of tatums."""

    start: float
    """The starting point (in seconds) of the time interval."""
    duration: float
    """The duration (in seconds) of the time interval."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the interval."""

class AudioAnalysisSection(BaseModel):
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

class AudioAnalysisSegment(BaseModel):
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

class AudioAnalysisTatum(BaseModel):
    """Audio analysis tatum.

    A tatum represents the lowest regular pulse train that a listener intuitively infers from the timing
    of perceived musical events (segments)."""

    start: float
    """The starting point (in seconds) of the time interval."""
    duration: float
    """The duration (in seconds) of the time interval."""
    confidence: float
    """The confidence, from 0.0 to 1.0, of the reliability of the interval."""

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

class SimpleChapter(BaseModel):
    audio_preview_url: str | None
    """A URL to a 30 second preview (MP3 format) of the chapter. `None` if not available."""
    available_markets: list[str] | None
    """A list of the countries in which the chapter can be played, identified by
    their [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code."""
    chapter_number: int
    """The number of the chapter."""
    description: str
    """A description of the chapter. HTML tags are stripped away from this field, use the ``html_description`` field in case HTML tags are needed."""
    html_description: str
    """A description of the chapter. This field may contain HTML tags."""
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
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
    is_playable: bool | None = None
    """`True` if the chapter is playable in the given market. Otherwise `False`."""
    languages: list[str]
    """A list of the languages used in the chapter, identified by their `ISO 639-1 code <https://en.wikipedia.org/wiki/ISO_639>`_."""
    name: str
    """The name of the chapter."""
    release_date: datetime.date | None
    """The date the chapter was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which ``release_date`` value is known."""
    resume_point: ResumePoint | None
    """The user's most recent position in the chapter. Set if the supplied access token is a user token and has the scope 'user-read-playback-position'."""
    uri: str
    """The Spotify URI for the chapter."""
    restrictions: Restrictions | None = None
    """Present when a content restriction is applied."""

class Chapter(SimpleChapter):
    """A chapter."""

    audiobook: SimpleAudiobook
    """The audiobook on which this chapter appears."""

class Copyright(BaseModel):
    """Copyright statements."""

    text: str
    """The copyright text for this content."""
    type: enums.CopyrightType
    """The type of copyright."""

class SavedEpisode(BaseModel):
    added_at: datetime.datetime
    """The date and time the episode was saved."""
    episode: Episode
    """The episode."""

class SimpleEpisode(BaseModel):
    """An episode."""

    audio_preview_url: str | None
    """A URL to a 30 second preview (MP3 format) of the episode. `None` if not available."""
    description: str
    """A description of the episode. HTML tags are stripped away from this field, use the ``html_description`` field in case HTML tags are needed."""
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
    """True if the episode is hosted outside of Spotify's CDN."""
    is_playable: bool | None = None
    """True if the episode is playable in the given market. Otherwise false. May be None in some situations."""
    languages: list[str]
    """A list of the languages used in the episode, identified by their `ISO 639-1 code <https://en.wikipedia.org/wiki/ISO_639>`_."""
    name: str
    """The name of the episode."""
    release_date: datetime.date
    """The date the episode was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which ``release_date`` value is known."""
    resume_point: ResumePoint | None = None
    """The user's most recent position in the episode. Set if the supplied access token is a user token and has the scope 'user-read-playback-position'."""
    uri: str
    """The Spotify URI for the episode."""
    restrictions: Restrictions | None = None
    """Present when a content restriction is applied."""

class Episode(SimpleEpisode):
    """An episode."""

    show: SimpleShow
    """The show on which this episode appears."""

class ExplicitContent(BaseModel):
    """Explicit content settings."""

    filter_enabled: bool
    """When ``True``, indicates that explicit content should not be played."""
    filter_locked: bool
    """When ``True``, indicates that the explicit content setting is locked and can't be changed by the user."""


class ExternalIDs(BaseModel):
    """External IDs."""

    isrc: str | None = None
    """[International Standard Recording Code](http://en.wikipedia.org/wiki/International_Standard_Recording_Code/)"""
    ean: str | None = None
    """[International Article Number](https://en.wikipedia.org/wiki/International_Article_Number_%28EAN%29)"""
    upc: str | None = None
    """[Universal Product Code](http://en.wikipedia.org/wiki/Universal_Product_Code)"""


class ExternalURLs(BaseModel):
    """External URLs."""

    spotify: str | None
    """The Spotify URL for the object."""

class Followers(BaseModel):
    """Information about followers."""

    href: str | None
    """This will always be set to `None`, as the Web API does not support it at the moment."""
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
    """Author information."""

    name: str
    """The name of the narrator."""


class PlayerTrack(BaseModel):
    context: Context | None
    timestamp: datetime.datetime
    progress: datetime.timedelta | None = pydantic.Field(alias="progress_ms")
    is_playing: bool
    item: TrackWithSimpleArtist | Episode | None
    currently_playing_type: enums.PlayingType
    actions: Actions

    @pydantic.field_validator("currently_playing_type", mode="before", check_fields=False)
    @classmethod
    def currently_playing_type_validator(cls, v: str) -> str:
        return v if v in ("track", "episode", "ad") else "unknown"

    @pydantic.field_validator("progress", mode="before", check_fields=False)
    @classmethod
    def progress_validator(cls, v: int) -> float:
        return v / 1000
    
class Player(PlayerTrack):
    device: Device
    repeat_state: enums.RepeatState
    shuffle_state: bool

    
class Device(BaseModel):
    id: str | None
    is_active: bool
    is_private_session: bool
    is_restricted: bool
    name: str
    # NOTE: I did not add an enum for this field as there no official list of values
    # [This](https://github.com/spotify/web-api/issues/687#issuecomment-358783650) list from 2018 exists,
    # but I don't trust that it is up to date.
    type: str
    volume_percent: int | None
    supports_volume: bool

class Context(BaseModel):
    type: enums.ContextType
    href: str
    external_urls: ExternalURLs
    uri: str

class Actions(BaseModel):
    interrupting_playback: bool | None = None
    pausing: bool | None = None
    resuming: bool | None = None
    seeking: bool | None = None
    skipping_next: bool | None = None
    skipping_prev: bool | None = None
    toggling_repeat_context: bool | None = None
    toggling_shuffle: bool | None = None
    toggling_repeat_track: bool | None = None
    transferring_playback: bool | None = None

class PlayHistory(BaseModel):
    track: TrackWithSimpleArtist
    played_at: datetime.datetime
    context: Context

class Queue(BaseModel):
    currently_playing: Track | Episode | None
    queue: list[Track | Episode]

class SimplePlaylist(BaseModel):
    """A simplified playlist."""

    collaborative: bool
    """``True`` if the owner allows other users to modify the playlist."""
    description: str | None
    """The playlist description. Only returned for modified, verified playlists, otherwise ``None``."""
    external_urls: ExternalURLs
    """Known external URLs for this playlist."""
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
    """The playlist's public/private status
    - true the playlist is public
    - false the playlist is private
    - null the playlist status is not relevant.
    """
    snapshot_id: str
    """The version identifier for the current playlist. Can be supplied in other requests to target a specific playlist version."""
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
    along with the total number of tracks in the playlist. Note, a track object may be null.
    This can happen if a track is no longer available.
    """

    href: str
    """A link to the Web API endpoint where full details of the playlist's tracks can be retrieved."""
    total: int
    """Number of tracks in the playlist."""

class PlaylistItem(BaseModel):
    added_at: datetime.datetime | None
    added_by: SimpleUser | None
    is_local: bool
    track: PlaylistTrack | Episode | None

class Playlists(BaseModel):
    message: str
    playlists: Paginator[SimplePlaylist]

class BasePaginator(
    BaseModel,
    typing.Generic[T],
):
    """A paginator with helpful methods to paginate through large amounts of content."""

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

class Paginator(BasePaginator[T]):
    offset: int
    """The offset of the items returned."""
    previous: str | None
    """URL to the previous page of items."""

class CursorPaginator(BasePaginator[T]):
    cursors: Cursors
    total: int | None = None  # pyright: ignore[reportIncompatibleVariableOverride]

class Cursors(BaseModel):
    """The cursors used to find the next set of items."""
    
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
        return (
            v if v in ("market", "product", "explicit", "payment_required")
            else "unknown"
        )

class ResumePoint(BaseModel):
    """Resume point information."""

    fully_played: bool
    """Whether or not the episode has been fully played by the user."""
    resume_position: datetime.timedelta = pydantic.Field(alias="resume_position_ms")
    """The user's most recent position in the episode."""

class SavedShow(BaseModel):
    added_at: datetime.datetime
    """The date and time the show was saved."""
    show: SimpleShow
    """The show."""

class SimpleShow(BaseModel):
    """A simplified show."""

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
    total_episodes: int
    """The total number of episodes in the show."""

class Show(SimpleShow):
    """A show."""

    episodes: Paginator[SimpleEpisode]
    """The episodes of the show."""

class SearchResult(BaseModel):
    tracks: Paginator[TrackWithSimpleArtist] | None = None
    artists: Paginator[Artist] | None = None
    albums: Paginator[SimpleAlbum] | None = None
    playlists: Paginator[SimplePlaylist] | None = None
    # NOTE: the unique `SimpleShow | None` below is to ignore/bypass an error caused by the spotify API
    # where it returns `null` objects instead of `Show` objects
    shows: Paginator[SimpleShow | None] | None = None
    episodes: Paginator[SimpleEpisode] | None = None
    audiobooks: Paginator[SimpleAudiobook] | None = None

class SavedTrack(BaseModel):
    """Information about an track saved to a user's "Your Music" library."""

    added_at: datetime.datetime
    """The date and time the track was saved."""
    track: TrackWithSimpleArtist
    """The track."""

class LinkedFromTrack(BaseModel):
    external_urls: ExternalURLs
    """Known external URLs for this track."""
    href: str
    """A link to the Web API endpoint providing full details of the track."""
    id: str
    """The Spotify ID for the track."""
    uri: str
    """The Spotify URI for the track."""

class TrackBase(LinkedFromTrack, typing.Generic[ArtistT]):
    artists: list[ArtistT]
    """The artists who performed the track."""
    available_markets: list[str] | None = None
    """A list of the countries in which the track can be played, identified by their `ISO 3166-1 alpha-2 code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
    Returns ``None`` if a market was specified in the request."""
    disc_number: int
    """The disc number (usually ``1`` unless the album consists of more than one disc)."""
    duration: datetime.timedelta = pydantic.Field(alias="duration_ms")
    """The track length."""
    explicit: bool
    """Whether or not the track has explicit lyrics."""
    is_playable: bool | None = None
    """Whether or not the track is playable in the given market.
    Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied."""
    linked_from: LinkedFromTrack | None = None
    """Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied, and the requested track has been replaced with a different track.
    The track in the linked_from object contains information about the originally requested track."""
    restrictions: Restrictions | None = None
    """Present when restrictions are applied to the track."""
    name: str
    """The name of the track."""
    preview_url: str | None
    """A link to a 30 second preview (MP3 format) of the track. Can be ``None``"""
    track_number: int
    """The number of the track. If an album has several discs, the track number is the number on the specified disc."""
    is_local: bool
    """Whether or not the track is from a local file."""

class SimpleTrack(TrackBase[SimpleArtist]):
    """A simplified track."""

class FullTrack(TrackBase[ArtistT], typing.Generic[ArtistT]):
    """A track."""

    album: SimpleAlbum
    """The album on which the track appears."""
    external_ids: ExternalIDs
    """Known external IDs for the track."""
    popularity: int
    """The popularity of the track. The value will be between 0 and 100, with 100 being the most popular."""

class Track(FullTrack[Artist]):
    ...

class TrackWithSimpleArtist(FullTrack[SimpleArtist]):
    ...

class PlaylistTrack(TrackBase[SimpleArtist]):
    """A track."""

    album: SimpleAlbum
    """The album on which the track appears."""
    external_ids: ExternalIDs
    """Known external IDs for the track."""
    popularity: int
    """The popularity of the track. The value will be between 0 and 100, with 100 being the most popular."""

class SimpleUser(BaseModel):
    external_urls: ExternalURLs
    """Known external URLs for this user."""
    followers: Followers | None = None
    """Information about the followers of the user."""
    href: str
    """A link to the Web API endpoint for this user."""
    id: str
    """The Spotify user ID for the user."""
    uri: str
    """The Spotify URI for the user."""

class User(SimpleUser):
    display_name: str | None
    """The name displayed on the user's profile. ``None`` if not available."""

class OwnUser(User):
    """A user."""

    country: str | None = None
    """The country of the user, as set in the user's account profile. An `ISO 3166-1 alpha-2 country code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
    This field is only available when the current user has granted access to the ``user-read-private`` scope."""
    email: str | None = None
    """The user's email address, as entered by the user when creating their account.
    This field is only available when the current user has granted access to the `user-read-email` scope.
    
    .. warning::

        This email address is unverified; there is no proof that it actually belongs to the user."""
    explicit_content: ExplicitContent | None = None
    """The user's explicit content settings. This field is only available when the current user has granted access to the `user-read-private` scope."""
    images: list[Image]
    """The user's profile image."""
    product: enums.SubscriptionLevel | None = None
    """The user's Spotify subscription level: "premium", "free", etc. (The subscription level "open" can be considered the same as "free".)
    This field is only available when the current user has granted access to the user-read-private scope."""

    @pydantic.field_validator("product", mode="before", check_fields=False)
    @classmethod
    def product_validator(cls, v: str) -> str:
        return "free" if v == "open" else v

class Recommendations(BaseModel):
    """Recommendations."""

    seeds: list[RecommendationsSeed]
    """A list of recommendation seed objects."""
    tracks: list[Track]
    """A list of simplified track objects."""

class RecommendationsSeed(BaseModel):
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
