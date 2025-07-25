/**
 * Infrastructure layer for S3 operations using AWS SDK
 */

import { S3Client as AWSS3Client, S3ClientConfig } from "@aws-sdk/client-s3";
import {
  ListObjectsV2Command,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectsCommand,
  HeadObjectCommand,
} from "@aws-sdk/client-s3";

import type {
  S3Config,
  ListCommand,
  UploadCommand,
  DownloadCommand,
  DeleteCommand,
  InfoCommand,
  ListResult,
  UploadResult,
  DownloadResult,
  DeleteResult,
  InfoResult,
} from './domain.ts';

export class S3Client {
  private client: AWSS3Client;
  private bucket: string;

  constructor(config: S3Config) {
    const s3Config: S3ClientConfig = {
      region: config.region,
      credentials: {
        accessKeyId: config.accessKeyId,
        secretAccessKey: config.secretAccessKey,
      },
    };

    if (config.endpoint) {
      s3Config.endpoint = config.endpoint;
      s3Config.forcePathStyle = true; // Required for MinIO and other S3-compatible services
    }

    this.client = new AWSS3Client(s3Config);
    this.bucket = config.bucket;
  }

  async listObjects(command: ListCommand): Promise<ListResult> {
    const response = await this.client.send(new ListObjectsV2Command({
      Bucket: this.bucket,
      Prefix: command.prefix,
      MaxKeys: command.maxKeys,
      ContinuationToken: command.continuationToken,
    }));

    return {
      type: 'list',
      objects: (response.Contents || []).map(obj => ({
        key: obj.Key!,
        lastModified: obj.LastModified!,
        size: obj.Size!,
        etag: obj.ETag,
        storageClass: obj.StorageClass,
      })),
      continuationToken: response.NextContinuationToken,
      isTruncated: response.IsTruncated || false,
    };
  }

  async uploadObject(command: UploadCommand): Promise<UploadResult> {
    // Convert string content to Uint8Array if needed
    const body = typeof command.content === 'string' 
      ? new TextEncoder().encode(command.content)
      : command.content;

    const response = await this.client.send(new PutObjectCommand({
      Bucket: this.bucket,
      Key: command.key,
      Body: body,
      ContentType: command.contentType,
      Metadata: command.metadata,
    }));

    return {
      type: 'upload',
      key: command.key,
      etag: response.ETag!,
      versionId: response.VersionId,
    };
  }

  async downloadObject(command: DownloadCommand): Promise<DownloadResult> {
    const response = await this.client.send(new GetObjectCommand({
      Bucket: this.bucket,
      Key: command.key,
    }));

    const bodyBytes = await response.Body!.transformToByteArray();
    
    // If outputPath is specified, save to file
    if (command.outputPath) {
      await Deno.writeFile(command.outputPath, bodyBytes);
      return {
        type: 'download',
        key: command.key,
        savedTo: command.outputPath,
        contentType: response.ContentType,
        metadata: response.Metadata,
      };
    } else {
      // Return content as string
      const content = new TextDecoder().decode(bodyBytes);
      return {
        type: 'download',
        key: command.key,
        content,
        contentType: response.ContentType,
        metadata: response.Metadata,
      };
    }
  }

  async deleteObjects(command: DeleteCommand): Promise<DeleteResult> {
    const response = await this.client.send(new DeleteObjectsCommand({
      Bucket: this.bucket,
      Delete: {
        Objects: command.keys.map(key => ({ Key: key })),
      },
    }));

    return {
      type: 'delete',
      deleted: (response.Deleted || []).map(obj => obj.Key!),
      errors: (response.Errors || []).map(err => ({
        key: err.Key!,
        error: `${err.Code}: ${err.Message}`,
      })),
    };
  }

  async getObjectInfo(command: InfoCommand): Promise<InfoResult> {
    try {
      const response = await this.client.send(new HeadObjectCommand({
        Bucket: this.bucket,
        Key: command.key,
      }));

      return {
        type: 'info',
        key: command.key,
        exists: true,
        size: response.ContentLength,
        lastModified: response.LastModified,
        contentType: response.ContentType,
        metadata: response.Metadata,
      };
    } catch (error: any) {
      if (error.name === 'NotFound') {
        return {
          type: 'info',
          key: command.key,
          exists: false,
        };
      }
      throw error;
    }
  }
}