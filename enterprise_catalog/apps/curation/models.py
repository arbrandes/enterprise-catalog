from uuid import uuid4

from django.db import models
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from enterprise_catalog.apps.catalog.constants import COURSE, PROGRAM
from enterprise_catalog.apps.catalog.models import ContentMetadata


class EnterpriseCurationConfig(TimeStampedModel):
    """
    Top-level container for all curations related to an enterprise.
    What's nice about this model:
    * Top-level container to hold anything related to catalog curation for an enterprise
    (there might be a time where we want types of curation besides highlights).
    * Gives us place to grow horizontally for fields related to a single enterprise's curation behavior.

    .. no_pii:
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )
    title = models.CharField(
        max_length=255,
        blank=False,
        null=False,
    )
    enterprise_uuid = models.UUIDField(
        blank=False,
        null=False,
        unique=True,
        db_index=True,
    )
    is_highlight_feature_active = models.BooleanField(
        null=False,
        default=True,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Enterprise curation")
        verbose_name_plural = _("Enterprise curations")
        app_label = 'curation'


class HighlightSet(TimeStampedModel):
    """
    One enterprise curation may produce multiple catalog highlight sets.
    What's nice about this model:
    * Could have multiple highlight sets per customer.
    * Could have multiple highlight sets per catalog (maybe we don't want to allow this now, but
    we might want it for highlight cohorts later).

    .. no_pii:
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )
    title = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        # It was decided during a 2022-11-08 standup to allow duplicate-named HighlightSets, at least for the MVP.
        unique=False,
    )
    enterprise_curation = models.ForeignKey(
        EnterpriseCurationConfig,
        blank=False,
        null=False,
        related_name='catalog_highlights',
        on_delete=models.deletion.CASCADE,
    )
    # can the learners see it?
    is_published = models.BooleanField(
        default=False,
        null=False,
    )
    history = HistoricalRecords()

    class Meta:
        app_label = 'curation'

    @property
    def card_image_url(self):
        """
        Returns the card image URL representing this highlight set.

        Notes:
        * `card_image_url` is derived by using the image of the earliest content added by the enterprise admin.  That
          way, the image is deterministic, and relatively stable after subsequent modifications of the highlight set
          selections.  After the initial highlight set creation, the only thing that can change the highlight set card
          image is removal of the first content added.

        Returns:
            str: URL of the selected card image.  None if no card image is found.
        """
        # In our add_content() view function, multiple requested content keys may be added in the same transaction, but
        # in practice that still results in distinct `created` values, which means we can still use that field for
        # sorting without worrying about duplicates.
        sorted_content = self.highlighted_content.order_by('created')

        # Finally, pick an image.  Ostensibly, it's that of the first highlighted content, but we also want to make sure
        # that we pick an existing card image.
        for content in sorted_content:
            url = content.card_image_url
            if url:
                return url

        # At this stage, one of the following must be true:
        #   * this highlight set does not contain any content, or
        #   * no content in this highlight set contains a card image.
        return None


class HighlightedContent(TimeStampedModel):
    """
    One HighlightSet can contain 0 or more HighlightedContent records.

    What's nice about this model:
    * Can highlight any kind of content that lives in enterprise-catalog
    (courses, programs, or course runs if necessary - though maybe we want to block that?)
    * Can use counts() in views that add highlights to enforce a max highlight content count per set.

    TODO: is there a way to easily record which catalog(s) were applicable for the enterprise
    when some content was added to the highlight set?

    .. no_pii:
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )
    catalog_highlight_set = models.ForeignKey(
        HighlightSet,
        blank=False,
        null=True,
        related_name='highlighted_content',
        on_delete=models.deletion.CASCADE,
    )
    content_metadata = models.ForeignKey(
        ContentMetadata,
        blank=False,
        null=True,
        related_name='highlighted_content',
        on_delete=models.deletion.CASCADE,
    )
    history = HistoricalRecords()

    class Meta:
        app_label = 'curation'
        unique_together = ('catalog_highlight_set', 'content_metadata')

    @property
    def content_type(self):
        """
        Returns the content type of the associated ContentMetadata.
        """
        if not self.content_metadata:
            return None
        return self.content_metadata.content_type

    @property
    def content_key(self):
        """
        Returns the content key of the associated ContentMetadata.
        """
        if not self.content_metadata:
            return None
        return self.content_metadata.content_key

    @property
    def title(self):
        """
        Returns the title from the raw metadata of the associated ContentMetadata object.

        TODO: handle `COURSERUN` and `LEARNER_PATHWAY`
        """
        if not self.content_metadata:
            return None
        return self.content_metadata.json_metadata.get('title')  # pylint: disable=no-member

    @property
    def card_image_url(self):
        """
        Returns the image URL from the raw metadata of the associated ContentMetadata object.

        Notes:
        * `COURSERUN` and `LEARNER_PATHWAY` content types are not supported, and result in `None`.

        Returns:
            str: URL of the card image.  None if no card image is found.
        """
        if not self.content_metadata:
            return None

        content_type = self.content_type
        if content_type == COURSE:
            return self.content_metadata.json_metadata.get('image_url')  # pylint: disable=no-member
        elif content_type == PROGRAM:
            return self.content_metadata.json_metadata.get('card_image_url')  # pylint: disable=no-member
        else:
            # Other possible content_types are `COURSERUN` and `LEARNER_PATHWAY`.
            return None

    @property
    def authoring_organizations(self):
        """
        Fetch the authoring organizations from the raw metadata of the associated ContentMetadata object.

        Notes:
        * There may be more than one authoring organization.
        * `COURSERUN` and `LEARNER_PATHWAY` content types are not supported, and result in an empty list.

        Returns:
            list of dict: Metadata about each authoring organization.
        """
        if not self.content_metadata:
            return []

        content_type = self.content_type
        owners = []
        if content_type == COURSE:
            owners = self.content_metadata.json_metadata.get('owners')  # pylint: disable=no-member
        elif content_type == PROGRAM:
            owners = self.content_metadata.json_metadata.get('authoring_organizations')  # pylint: disable=no-member

        return [
            {
                'uuid': owner['uuid'],
                'name': owner['name'],
                'logo_image_url': owner['logo_image_url'],
            }
            for owner in owners
        ]