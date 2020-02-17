import argparse
import boto3
import sys
import logging
import json


class Base:
    def __init__(self, name):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(funcName)s %(levelname)s :%(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.region = 'ap-northeast-1'
        self.name = name


class S3Client(Base):
    def __init__(self, name: str):
        super().__init__(name)
        self.cli = boto3.client('s3')
        self.arn_prefix = 'arn:aws:s3:::'

    def create(self):
        self.logger.info('Creating a S3...')
        try:
            res = self.cli.create_bucket(
                CreateBucketConfiguration={
                    'LocationConstraint': self.region
                },
                Bucket=self.name
            )
        except Exception as e:
            self.logger.error('Catch exception')
            self.logger.error(type(e))
            self.logger.error(e)
            return False

        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            self.logger.debug('Response: {}'.format(res))
            self.logger.info('Done.')
            return True
        else:
            self.logger.error('BadStatusCode')
            self.logger.error('Response: {}'.format(res))
            return False

    def get_arn(self):
        return self.arn_prefix + self.name


class IAMClient(Base):
    def __init__(self, name: str, base_policy: dict, s3arn: str):
        super().__init__(name)
        self.iam_user_prefix = 's3-'
        self.iam_user_suffix = '-user'
        self.cli = boto3.client('iam')
        self.policy = base_policy
        self.s3arn = s3arn

    def create_user(self):
        self.logger.info('Creating an IAM User...')
        self._add_s3_of_name_in_policy()
        try:
            create_user_res = self.cli.create_user(
                UserName=self.iam_user_prefix + self.name + self.iam_user_suffix
            )
        except Exception as e:
            self.logger.error('Catch exception')
            self.logger.error(type(e))
            self.logger.error(e)
            return dict()

        self.logger.debug('Response: {}'.format(create_user_res))
        policy_arn = self._create_policy(create_user_res['User']['UserName'])
        self._attach_policy_for_user(
            username=create_user_res['User']['UserName'],
            policy_arn=policy_arn
        )
        result = self._generate_key(create_user_res['User']['UserName'])
        self.logger.info('AccessKey: {}'.format(result['access_key']))
        self.logger.info('SecretKey: {}'.format(result['secret_key']))
        result['iam_username'] = create_user_res['User']['UserName']
        result['iam_policy_arn'] = policy_arn
        self.logger.info('Done')
        self.logger.info('Created: {}'.format(result))
        return result

    def _add_s3_of_name_in_policy(self):
        self.logger.info('Adding the s3 of name in policy...')
        self.logger.debug('Before: {}'.format(self.policy))
        try:
            for statement in self.policy['Statement']:
                path = statement['Resource']
                statement['Resource'] = self.s3arn + path
        except Exception as e:
            self.logger.error('Catch exception')
            self.logger.error(type(e))
            self.logger.error(e)
            return False

        self.logger.debug('After: {}'.format(self.policy))
        self.logger.info('Done')
        return True

    def _create_policy(self, prefix_name):
        self.logger.info('Creating a policy...')
        self.logger.debug(json.dumps(self.policy, indent=4))
        try:
            res = self.cli.create_policy(
                PolicyName=prefix_name + '-policy',
                PolicyDocument=json.dumps(self.policy, indent=4)
            )
            self.logger.debug(res)
            arn = res['Policy']['Arn']
        except Exception as e:
            self.logger.error('Catch exception')
            self.logger.error(type(e))
            self.logger.error(e)
            return str()

        self.logger.info('Done')
        return arn

    def _attach_policy_for_user(self, username, policy_arn):
        self.logger.info('Attaching a policy...')
        try:
            res = self.cli.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
        except Exception as e:
            self.logger.error('Catch exception')
            self.logger.error(type(e))
            self.logger.error(e)
            return False

        self.logger.debug('Attach Response: {}'.format(res))
        self.logger.info('Done')
        return True

    def _generate_key(self, username):
        self.logger.info('Generating a key...')
        try:
            res = self.cli.create_access_key(
                UserName=username
            )
            key = dict(
                access_key=res['AccessKey']['AccessKeyId'],
                secret_key=res['AccessKey']['SecretAccessKey']
            )
        except Exception as e:
            self.logger.error('Catch exception')
            self.logger.error(type(e))
            self.logger.error(e)
            return dict()

        self.logger.info('Done')
        return key

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='S3の作成とそのS3に対するアクセス権限を持つIAMUserを作成するプログラム'
    )
    parser.add_argument(
        '-n', '--name',
        help='S3とIAMに使用する名前',
        required=True
    )
    parser.add_argument(
        '-p', '--policy',
        help='基本となるポリシー',
        required=True
    )

    args = parser.parse_args()
    s3cli = S3Client(args.name)
    if s3cli.create() is False:
        sys.exit()

    iamcli = IAMClient(
        name=args.name,
        base_policy=json.load(open(args.policy, 'r')),
        s3arn=s3cli.get_arn()
    )
    result = iamcli.create_user()
    result['s3name'] = args.name
    json_file = open('{}_state.json'.format(args.name), 'w')
    json.dump(result, json_file)
