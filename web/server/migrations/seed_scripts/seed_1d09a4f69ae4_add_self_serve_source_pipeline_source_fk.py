import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime

from web.server.data.data_access import Transaction
from . import get_session

# pylint: disable=C0103
Base = declarative_base()


class DataUploadFileSummary(Base):
    '''Represents the information about a single file uploaded through data upload'''

    __tablename__ = "data_upload_file_summary"

    id = sa.Column(sa.Integer(), primary_key=True)
    source_id = sa.Column(sa.String(100), nullable=False)
    file_path = sa.Column(sa.Text(), nullable=False)
    # Storing the user's original file name since we rename the file for reference internally.
    # This allows the displayed name to be as the user expects.
    user_file_name = sa.Column(sa.Text(), nullable=False)
    column_mapping = sa.Column(JSONB(), nullable=False)

    created = sa.Column(DateTime, nullable=False, server_default=sa.func.now())
    last_modified = sa.Column(
        DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
    )


class DataprepFlow(Base):
    '''Represents a dataprep flow for each source that has the required information to trigger a
    dataprep job and also validate an uploaded dataprep file.
    '''

    __tablename__ = "dataprep_flow"

    id = sa.Column(sa.Integer(), primary_key=True)
    expected_columns = sa.Column(JSONB(), nullable=False)
    recipe_id = sa.Column(sa.Integer(), unique=True, nullable=False)
    jobs = relationship(
        'DataprepJob', order_by='DataprepJob.created.desc()', backref='dataprep_flow'
    )


class DataprepJob(Base):
    '''Represents information about a single dataprep job.'''

    __tablename__ = "dataprep_job"

    id = sa.Column(sa.Integer(), primary_key=True)
    created_on_dataprep = sa.Column(DateTime, nullable=False)
    last_modified_on_dataprep = sa.Column(DateTime, nullable=False)
    job_id = sa.Column(sa.Integer(), unique=True, nullable=False)
    status = sa.Column(sa.String(100), nullable=True)
    dataprep_flow_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey('dataprep_flow.id', ondelete='CASCADE'),
        nullable=False,
    )

    created = sa.Column(DateTime, nullable=False, server_default=sa.func.now())
    last_modified = sa.Column(
        DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
    )


class SelfServeSource(Base):
    '''Represents a data source configured and uploaded through the self-serve data
    upload tool
    '''

    __tablename__ = "self_serve_source"

    id = sa.Column(sa.Integer(), primary_key=True)
    source_id = sa.Column(sa.String(100), nullable=False)
    source_name = sa.Column(sa.String(100), nullable=False)
    # the source's current file
    file_summary_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey('data_upload_file_summary.id', ondelete='CASCADE'),
        nullable=False,
    )
    dataprep_flow_id = sa.Column(
        sa.Integer(), sa.ForeignKey('dataprep_flow.id', ondelete='CASCADE')
    )
    last_modified = sa.Column(
        DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
    )

    file_summary = relationship('DataUploadFileSummary')
    dataprep_flow = relationship('DataprepFlow')


class PipelineDatasource(Base):
    '''Represents a pipeline data source that produces the raw data.'''

    __tablename__ = 'pipeline_datasource'

    id = sa.Column(sa.String(), primary_key=True)
    name = sa.Column(sa.String(), nullable=False)


def upvert_data(alembic_operation):
    '''Adds a PipelineDatasource for every SelfServeSource that is not present'''
    with Transaction(get_session=lambda: get_session(alembic_operation)) as transaction:
        sources = transaction.find_all(SelfServeSource)
        for source in sources:
            if not transaction.find_by_id(PipelineDatasource, source.source_id):
                pipeline_datasource = PipelineDatasource(
                    id=source.source_id, name=source.source_name
                )
                transaction.add_or_update(pipeline_datasource)


def downvert_data(alembic_operation):
    '''Copies the PipelineDatasource name to the SelfServeSource'''
    with Transaction(get_session=lambda: get_session(alembic_operation)) as transaction:
        sources = transaction.find_all(SelfServeSource)
        for source in sources:
            pipeline_datasource = transaction.find_by_id(
                PipelineDatasource, source.source_id
            )
            if pipeline_datasource:
                source.source_name = pipeline_datasource.name
                transaction.add_or_update(source)
