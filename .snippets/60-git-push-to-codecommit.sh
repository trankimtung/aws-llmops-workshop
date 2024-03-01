#!/bin/sh
pip install git-remote-codecommit
git remote add ccm codecommit::us-east-1://llmops-workshop
git push ccm main
