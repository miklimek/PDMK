using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UIElements;

public class PlayerGestures : MonoBehaviour
{
    public Rigidbody2D rb { get; private set; }
    public float speed;

    private string url = "http://127.0.0.1:81/gestures";
    private string direction;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }
    private void FixedUpdate()
    {
        StartCoroutine(GetPlayerInput(url));

        if (direction == "Stop")
        {
            rb.velocity = new Vector2(0, rb.velocity.y);
        }
        else if (direction == "Left")
        {
            rb.velocity = new Vector2(-1 * speed, rb.velocity.y);
        }
        else if (direction == "Right")
        {
            rb.velocity = new Vector2(1 * speed, rb.velocity.y);
        }
    }

    IEnumerator GetPlayerInput(string url)
    {
        UnityWebRequest request = UnityWebRequest.Get(url);

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError(request.error);
            yield break;
        }
        string json = request.downloadHandler.text;

        direction = JsonUtility.FromJson<PlayerDirectionGestures>(json).direction;
    }
}
