# SBM Safety Boundary

1. DoctorはSBMの日次処理関数を呼び出さない。
2. SBMの日次処理中はCatalog出力とDoctor処置開始を拒否する。
3. DoctorはSBMの`記事管理`を直接更新しない。
4. 状態変更はDoctor Case JSONをSBMが受理した場合だけ行う。
5. Doctorの時間主導トリガー名・Propertiesキーは`Doctor`接頭辞を使用する。
6. Doctor失敗時もSBMの日次処理状態を変更しない。
