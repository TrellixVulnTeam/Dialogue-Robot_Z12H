"""
编辑距离
"""
import numpy as np


def edit_distance(word1, word2):
    len1 = len(word1)
    len2 = len(word2)
    dp = np.zeros((len1 + 1,len2 + 1))
    for i in range(len1 + 1):
        dp[i][0] = i    
    for j in range(len2 + 1):
        dp[0][j] = j
     
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            delta = 0 if word1[i-1] == word2[j-1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + delta, min(dp[i-1][j] + 1, dp[i][j - 1] + 1))

    return dp[len1][len2]

if __name__ == '__main__':
    print(edit_distance('123', '111'))
