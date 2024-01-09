using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

public class PlayerTangible : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; }
    public float speed;

    private string url = "http://127.0.0.1:81/tangible";
    private float position;

    private const int SCREENHALFWIDTH = 12;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void FixedUpdate()
    {
        StartCoroutine(GetPlayerPosition(url));
        Vector2 newPosition = new Vector2(SCREENHALFWIDTH * position, rb.position.y);
        float t = Vector2.Distance(rb.position, newPosition) / speed;

        rb.transform.position = Vector2.MoveTowards(rb.position, newPosition, t);
        //rb.transform.position = Vector2.MoveTowards(rb.position, newPosition, speed * Time.deltaTime);
    }

    IEnumerator GetPlayerPosition(string url)
    {
        UnityWebRequest request = UnityWebRequest.Get(url);

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error);
            yield break;
        }
        string json = request.downloadHandler.text;

        position = JsonUtility.FromJson<PlayerPositionTangible>(json).position;
    }
}
