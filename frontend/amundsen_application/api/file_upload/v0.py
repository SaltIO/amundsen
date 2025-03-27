# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from pkg_resources import iter_entry_points

from http import HTTPStatus

import boto3
from botocore.config import Config

from flask import Response, jsonify, make_response, current_app as app, request
from flask.blueprints import Blueprint
from werkzeug.utils import import_string

LOGGER = logging.getLogger(__name__)

file_upload_blueprint = Blueprint('file_upload', __name__, url_prefix='/api/file_upload/v0')

@file_upload_blueprint.route('/initiate_multipart_upload', methods=['POST'])
def initiate_multipart_upload():

    data = request.json
    file_name = data.get('fileName')
    file_type = data.get('fileType')

    try:
        # Initiate multipart upload
        response = _get_s3_client().create_multipart_upload(
            Bucket=_get_bucket_name(),
            Key=_get_s3_file_key(file_name=file_name),
            ContentType=file_type
        )

        return make_response(jsonify({'uploadId': response['UploadId']}), HTTPStatus.OK)
    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        LOGGER.exception(message)
        payload = jsonify({'uploadId': '', 'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)


@file_upload_blueprint.route('/get_presigned_url', methods=['POST'])
def get_presigned_url() -> Response:
    data = request.json
    file_name = data.get('fileName')
    upload_id = data.get('uploadId')
    part_number = data.get('partNumber')  # The chunk/part number
    content_type = data.get('contentType')


    try:
        # Generate presigned URL for the specific part
        presigned_url = _get_s3_client().generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': _get_bucket_name(),
                'Key': _get_s3_file_key(file_name=file_name),
                'UploadId': upload_id,
                'PartNumber': part_number,
                # 'ContentType': content_type
            },
            ExpiresIn=3600  # 1 hour expiration
        )

        return make_response(jsonify({'url': presigned_url}), HTTPStatus.OK)

    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        LOGGER.exception(message)
        payload = jsonify({'url': '', 'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)

@file_upload_blueprint.route('/complete_multipart_upload', methods=['POST'])
def complete_multipart_upload():
    data = request.json
    file_name = data.get('fileName')
    upload_id = data.get('uploadId')
    parts = data.get('parts')  # List of parts {PartNumber, ETag}

    try:
        # Complete the multipart upload
        response = _get_s3_client().complete_multipart_upload(
            Bucket=_get_bucket_name(),
            Key=_get_s3_file_key(file_name=file_name),
            UploadId=upload_id,
            MultipartUpload={
                'Parts': parts
            }
        )

        message = f"*{app.config['HOST_ID']} - Metadata File Upload*\n{file_name}"
        _send_notification(message=message)

        return make_response(jsonify(response), HTTPStatus.OK)

    except Exception as e:
        message = 'Encountered exception: ' + str(e)
        LOGGER.exception(message)
        payload = jsonify({'msg': message})
        return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)


def _get_bucket_name() -> str:
    return f'cmdrvl-metadata-{app.config["HOST_ID"]}'

def _get_s3_client():
    s3_client = boto3.client(
        's3',
        region_name=app.config['AWS_DEFAULT_REGION'],
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4')
    )
    return s3_client

def _get_s3_file_key(file_name: str) -> str:
    return f'upload/{file_name}'

def _send_notification(message: str):
    if app.config.get('SLACK_CLIENT'):
        try:
            app.config['SLACK_CLIENT'].post(channel=app.config['SLACK_SUPPORT_CHANNEL'], message=message)
        except Exception as e:
            LOGGER.exception(f'Failed to send Slack Notification')