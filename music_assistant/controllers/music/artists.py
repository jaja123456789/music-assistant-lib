"""Manage MediaItems of type Artist."""

import asyncio
import itertools
from typing import Dict, List, Optional

from databases import Database as Db

from music_assistant.helpers.database import TABLE_ALBUMS, TABLE_ARTISTS, TABLE_TRACKS
from music_assistant.helpers.json import json_serializer
from music_assistant.models.enums import EventType, ProviderType
from music_assistant.models.event import MassEvent
from music_assistant.models.media_controller import MediaControllerBase
from music_assistant.models.media_items import (
    Album,
    AlbumType,
    Artist,
    ItemMapping,
    MediaType,
    Track,
)
from music_assistant.models.music_provider import MusicProvider


class ArtistsController(MediaControllerBase[Artist]):
    """Controller managing MediaItems of type Artist."""

    db_table = TABLE_ARTISTS
    media_type = MediaType.ARTIST
    item_cls = Artist

    async def toptracks(
        self,
        item_id: str,
        provider: Optional[ProviderType] = None,
        provider_id: Optional[str] = None,
    ) -> List[Track]:
        """Return top tracks for an artist."""
        artist = await self.get(item_id, provider, provider_id)
        # get results from all providers
        coros = [
            self.get_provider_artist_toptracks(item.item_id, item.prov_id)
            for item in artist.provider_ids
        ]
        tracks = itertools.chain.from_iterable(await asyncio.gather(*coros))
        # merge duplicates using a dict
        final_items: Dict[str, Track] = {}
        for track in tracks:
            key = f".{track.name}.{track.version}"
            if key in final_items:
                final_items[key].provider_ids.update(track.provider_ids)
            else:
                final_items[key] = track
        return list(final_items.values())

    async def albums(
        self,
        item_id: str,
        provider: Optional[ProviderType] = None,
        provider_id: Optional[str] = None,
    ) -> List[Album]:
        """Return (all/most popular) albums for an artist."""
        artist = await self.get(item_id, provider, provider_id)
        # get results from all providers
        coros = [
            self.get_provider_artist_albums(item.item_id, item.prov_id)
            for item in artist.provider_ids
        ]
        albums = itertools.chain.from_iterable(await asyncio.gather(*coros))
        # merge duplicates using a dict
        final_items: Dict[str, Album] = {}
        for album in albums:
            key = f".{album.name}.{album.version}"
            if key in final_items:
                final_items[key].provider_ids.update(album.provider_ids)
            else:
                final_items[key] = album
            if album.in_library:
                final_items[key].in_library = True
        return list(final_items.values())

    async def add(self, item: Artist) -> Artist:
        """Add artist to local db and return the database item."""
        # grab musicbrainz id and additional metadata
        await self.mass.metadata.get_artist_metadata(item)
        db_item = await self.add_db_item(item)
        # also fetch same artist on all providers
        await self.match_artist(db_item)
        db_item = await self.get_db_item(db_item.item_id)
        return db_item

    async def match_artist(self, db_artist: Artist):
        """
        Try to find matching artists on all providers for the provided (database) item_id.

        This is used to link objects of different providers together.
        """
        assert (
            db_artist.provider == ProviderType.DATABASE
        ), "Matching only supported for database items!"
        cur_prov_types = {x.prov_type for x in db_artist.provider_ids}
        for provider in self.mass.music.providers:
            if provider.type in cur_prov_types:
                continue
            if MediaType.ARTIST not in provider.supported_mediatypes:
                continue
            if await self._match(db_artist, provider):
                cur_prov_types.add(provider.type)
            else:
                self.logger.debug(
                    "Could not find match for Artist %s on provider %s",
                    db_artist.name,
                    provider.name,
                )

    async def get_provider_artist_toptracks(
        self, item_id: str, provider_id: str
    ) -> List[Track]:
        """Return top tracks for an artist on given provider."""
        prov = self.mass.music.get_provider(provider_id)
        if not prov:
            return []
        # prefer cache items (if any)
        cache_key = f"{prov.type.value}.artist_toptracks.{item_id}"
        if cache := await self.mass.cache.get(cache_key):
            return [Track.from_dict(x) for x in cache]
        # no items in cache - get listing from provider
        items = await prov.get_artist_toptracks(item_id)
        # store (serializable items) in cache
        self.mass.create_task(
            self.mass.cache.set(cache_key, [x.to_dict() for x in items])
        )
        return items

    async def get_provider_artist_albums(
        self, item_id: str, provider_id: str
    ) -> List[Album]:
        """Return albums for an artist on given provider."""
        prov = self.mass.music.get_provider(provider_id)
        if not prov:
            return []
        # prefer cache items (if any)
        cache_key = f"{prov.type.value}.artist_albums.{item_id}"
        if cache := await self.mass.cache.get(cache_key):
            return [Album.from_dict(x) for x in cache]
        # no items in cache - get listing from provider
        items = await prov.get_artist_albums(item_id)
        # store (serializable items) in cache
        self.mass.create_task(
            self.mass.cache.set(cache_key, [x.to_dict() for x in items])
        )
        return items

    async def add_db_item(
        self, item: Artist, overwrite_existing: bool = False, db: Optional[Db] = None
    ) -> Artist:
        """Add a new item record to the database."""
        assert item.provider_ids, "Album is missing provider id(s)"
        async with self.mass.database.get_db(db) as db:
            # always try to grab existing item by musicbrainz_id
            cur_item = None
            if item.musicbrainz_id:
                match = {"musicbrainz_id": item.musicbrainz_id}
                cur_item = await self.mass.database.get_row(self.db_table, match, db=db)
            if not cur_item:
                # fallback to matching
                # NOTE: we match an artist by name which could theoretically lead to collisions
                # but the chance is so small it is not worth the additional overhead of grabbing
                # the musicbrainz id upfront
                match = {"sort_name": item.sort_name}
                for row in await self.mass.database.get_rows(
                    self.db_table, match, db=db
                ):
                    row_artist = Artist.from_db_row(row)
                    if row_artist.sort_name == item.sort_name:
                        # just to be sure ?!
                        cur_item = row_artist
                        break
            if cur_item:
                # update existing
                return await self.update_db_item(
                    cur_item.item_id, item, overwrite=overwrite_existing, db=db
                )

            # insert item
            new_item = await self.mass.database.insert(
                self.db_table, item.to_db_row(), db=db
            )
            item_id = new_item["item_id"]
            self.logger.debug("added %s to database", item.name)
            # return created object
            db_item = await self.get_db_item(item_id, db=db)
            self.mass.signal_event(
                MassEvent(
                    EventType.MEDIA_ITEM_ADDED, object_id=db_item.uri, data=db_item
                )
            )
            return db_item

    async def update_db_item(
        self,
        item_id: int,
        item: Artist,
        overwrite: bool = False,
        db: Optional[Db] = None,
    ) -> Artist:
        """Update Artist record in the database."""
        cur_item = await self.get_db_item(item_id)
        if overwrite:
            metadata = item.metadata
            provider_ids = item.provider_ids
        else:
            metadata = cur_item.metadata.update(item.metadata)
            provider_ids = {*cur_item.provider_ids, *item.provider_ids}

        async with self.mass.database.get_db(db) as db:
            await self.mass.database.update(
                self.db_table,
                {"item_id": item_id},
                {
                    "name": item.name if overwrite else cur_item.name,
                    "sort_name": item.sort_name if overwrite else cur_item.sort_name,
                    "musicbrainz_id": item.musicbrainz_id or cur_item.musicbrainz_id,
                    "metadata": json_serializer(metadata),
                    "provider_ids": json_serializer(provider_ids),
                },
                db=db,
            )
            self.logger.debug("updated %s in database: %s", item.name, item_id)
            db_item = await self.get_db_item(item_id, db=db)
            self.mass.signal_event(
                MassEvent(
                    EventType.MEDIA_ITEM_UPDATED, object_id=db_item.uri, data=db_item
                )
            )
            return db_item

    async def delete_db_item(self, item_id: int, db: Optional[Db] = None) -> None:
        """Delete record from the database."""

        # delete tracks/albums connected to this artist
        async with self.mass.database.get_db(db) as db:
            await self.mass.database.delete_where_query(
                TABLE_TRACKS, f"artists LIKE '%\"{item_id}\"%'", db=db
            )
            await self.mass.database.delete_where_query(
                TABLE_ALBUMS, f"artists LIKE '%\"{item_id}\"%'", db=db
            )
        # delete the artist itself from db
        await super().delete_db_item(item_id, db)

        self.logger.debug("deleted item with id %s from database", item_id)

    async def _match(self, db_artist: Artist, provider: MusicProvider) -> bool:
        """Try to find matching artists on given provider for the provided (database) artist."""
        self.logger.debug(
            "Trying to match artist %s on provider %s", db_artist.name, provider.name
        )
        # try to get a match with some reference tracks of this artist
        for ref_track in await self.toptracks(db_artist.item_id, db_artist.provider):
            # make sure we have a full track
            if isinstance(ref_track.album, ItemMapping):
                ref_track = await self.mass.music.tracks.get(
                    ref_track.item_id, ref_track.provider
                )
            for search_str in (
                f"{db_artist.name} - {ref_track.name}",
                f"{db_artist.name} {ref_track.name}",
                ref_track.name,
            ):
                search_results = await self.mass.music.tracks.search(
                    search_str, provider.type
                )
                for search_result_item in search_results:
                    if search_result_item.sort_name != ref_track.sort_name:
                        continue
                    # get matching artist from track
                    for search_item_artist in search_result_item.artists:
                        if search_item_artist.sort_name != db_artist.sort_name:
                            continue
                        # 100% album match
                        # get full artist details so we have all metadata
                        prov_artist = await self.get_provider_item(
                            search_item_artist.item_id, search_item_artist.provider
                        )
                        await self.update_db_item(db_artist.item_id, prov_artist)
                        return True
        # try to get a match with some reference albums of this artist
        artist_albums = await self.albums(db_artist.item_id, db_artist.provider)
        for ref_album in artist_albums:
            if ref_album.album_type == AlbumType.COMPILATION:
                continue
            if ref_album.artist is None:
                continue
            for search_str in (
                ref_album.name,
                f"{db_artist.name} - {ref_album.name}",
                f"{db_artist.name} {ref_album.name}",
            ):
                search_result = await self.mass.music.albums.search(
                    search_str, provider.type
                )
                for search_result_item in search_result:
                    if search_result_item.artist is None:
                        continue
                    if search_result_item.sort_name != ref_album.sort_name:
                        continue
                    # artist must match 100%
                    if (
                        search_result_item.artist.sort_name
                        != ref_album.artist.sort_name
                    ):
                        continue
                    # 100% match
                    # get full artist details so we have all metadata
                    prov_artist = await self.get_provider_item(
                        search_result_item.artist.item_id,
                        search_result_item.artist.provider,
                    )
                    await self.update_db_item(db_artist.item_id, prov_artist)
                    return True
        return False
