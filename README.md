# S3作って、それに対するIAM発行するもの

表題の通りです。

# 環境

- python 3.7.4
- pyenv 1.2.13-17-g38de38e3

# 使い方

以下のように実行して下さい。

```
$ python create_s3_and_issue_iam.py -n cm-fukazawa-sampleple -p base_terraform_policy.json
```

それぞれの引数の意味は次の通りです。
```
$ python create_s3_and_issue_iam.py -h
usage: create_s3_and_issue_iam.py [-h] -n NAME -p POLICY

S3の作成とそのS3に対するアクセス権限を持つIAMUserを作成するプログラム

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  S3とIAMに使用する名前
  -p POLICY, --policy POLICY
                        基本となるポリシー
```

最終的に<NAME>_state.jsonというファイルが出力されます。そちらに記載されているアクセスキーとシークレットキーをご利用下さい。

# ポリシーの書き方
Resourceのところにはプログラムが作成したバケット名を入れるので空欄にして下さい。  
オブジェクトが対象になる場合（GetObject, PutObject等）は対象へのPATHだけ記載して下さい。  
以下の例を参照して下さい。  
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": ""
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "/*"
    }
  ]
}
```
